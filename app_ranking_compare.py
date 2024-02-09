import argparse
import json

import database
from flask import Flask, render_template, request, redirect, session, flash, make_response, jsonify
from flask_login import login_user, LoginManager, logout_user, current_user
from mongoengine import *

from config import Config
import os
import logging
from src.evaluate.evaluate import get_fairness_metrics, get_utility_metrics, get_average_interactions

logging.basicConfig(filename='record.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder='./static')
app.config.from_object(Config)


# login_manager = LoginManager()
# login_manager.init_app(app)
parser = argparse.ArgumentParser()
parser.add_argument('--config_path')
args = parser.parse_args()
with open(args.config_path) as f:
    configs = json.load(f)

#connect('data', host='mongo', port=27017) #our mongodb database
connect(configs["data_reader_class"]["name"], host=f'mongodb://{"mongo-container"}:{27017}/{configs["data_reader_class"]["name"]}', port=27017)
#connect('data', host='0.0.0.0', port=27017)
#connect(configs["data_reader_class"]["name"], host=f'mongodb://{"mongo-container"}:{27017}/{configs["data_reader_class"]["name"]}', port=27017)
login_manager = LoginManager()
login_manager.init_app(app)


# login page
@login_manager.user_loader
def loader_user(_user_id):
    user = database.User.objects(_user_id=_user_id).first()
    return user


@app.route("/")
@app.route("/start_compare_annotate/<int:experiment_id>", methods=['GET', 'POST'])
def start_compare_annotate(experiment_id):
    if current_user.is_authenticated:
        session['user_id'] = current_user._user_id

        url = get_next_task_URL(experiment_id, 0)
        response = make_response(redirect(url, code=200))
        response.headers['HX-Redirect'] = url
        return response

    if request.method == 'POST':
        # record user in the db
        user_id = request.form['user_id']
        # create new user in the db
        new_user = database.User(_user_id=user_id)
        existing_document = database.User.objects(_user_id=new_user._user_id).first()
        if not existing_document:
            new_user.save()

        # create user session and redirect
        user = database.User.objects(_user_id=user_id).first()
        if user and user._user_id == user_id:
            login_user(current_user)
            session['user_id'] = user_id

            url = get_next_task_URL(experiment_id, 0)
            response = make_response(redirect(url, code=200))
            response.headers['HX-Redirect'] = url
            return response
        else:
            flash('Invalid user_id', 'danger')

    return render_template('start_compare.html')


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user();
    response = make_response(redirect('/login', code=200))
    response.headers['HX-Redirect'] = '/login'
    return response


@app.route("/")
@app.route("/start_compare/<int:experiment_id>", methods=['GET', 'POST'])
def start_compare(experiment_id):
    url = get_next_task_URL(experiment_id, 0)
    response = make_response(redirect(url, code=200))
    response.headers['HX-Redirect'] = url
    return response


def get_next_task_URL(exp_id, n_task):
    url = str(exp_id) + '/index_compare/' + str(n_task)
    return url


@app.route('/api/<experiment_id>/get_task/<direction>/<task_n>', methods=['GET'])
def get_task(experiment_id, direction, task_n):
    experiment = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    if direction == 'next':
        next_task = int(task_n) + 1
    else:
        next_task = int(task_n) - 1

    if next_task >= len(experiment.tasks):
        next_task = 0
    elif next_task == -1:
        next_task = len(experiment.tasks) - 1
    return jsonify({'next_task': str(next_task)})


@app.route("/start_compare/<experiment_id>/index_compare/<n_task>", methods=['GET', 'POST'])
def index_compare(experiment_id, n_task):
    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(n_task)]

    task_obj = database.TaskCompare.objects(_id=task_id).first()
    data_obj = database.Data.objects(_id=task_obj.data).first()
    query_obj = database.QueryRepr.objects(_id=data_obj.query).first()

    docs = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type_1][0].docs
    docs_obj_1 = [database.DocRepr.objects(_id=doc_id).first() for doc_id in docs]

    docs = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type_2][0].docs
    docs_obj_2 = [database.DocRepr.objects(_id=doc_id).first() for doc_id in docs]


    doc_field_names_display = configs["ui_display_config"]["display_fields"]


    query_title = query_obj.title
    query_text = query_obj.text

    current_url = '/start_compare/' + str(experiment_id) + '/index_compare/' + str(n_task) + '/'
    view_configs = configs["ui_display_config"]

    interactions = get_average_interactions(configs["ui_display_config"]["avg_interaction"]["experiment_id"], interaction=configs["ui_display_config"]["avg_interaction"]["interaction"])

    fairness_metrics = dict()
    utility_metrics = dict()
    if "display_metrics" in configs["ui_display_config"]:
        utility_metrics[task_obj.ranking_type_1] = get_utility_metrics(configs, query_title, docs_obj_1)
        utility_metrics[task_obj.ranking_type_2] = get_utility_metrics(configs, query_title, docs_obj_2)
        fairness_metrics[task_obj.ranking_type_1] = get_fairness_metrics(configs, docs_obj_1)
        fairness_metrics[task_obj.ranking_type_2] = get_fairness_metrics(configs, docs_obj_2)
    else:
        utility_metrics[task_obj.ranking_type_1] = []
        utility_metrics[task_obj.ranking_type_2] = []
        fairness_metrics[task_obj.ranking_type_1] = []
        fairness_metrics[task_obj.ranking_type_2] = []

    return render_template('index_ranking_compare_template.html', doc_field_names=doc_field_names_display,
                           avg_interaction = interactions, utility_metrics= utility_metrics, fairness_metrics=fairness_metrics,
                           view_configs=view_configs,
                           doc_data_objects_1=docs_obj_1, doc_data_objects_2=docs_obj_2,
                           ranking_type_1=task_obj.ranking_type_1, ranking_type_2=task_obj.ranking_type_2,
                           query_title=query_title, query_text=query_text, current_url=current_url, task_description=configs["ui_display_config"]["task_description"])






# @login_required


@app.route("/stop_experiment/", methods=['GET', 'POST'])
# @login_required
def stop_experiment():
    return render_template('stop_experiment_template.html')


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True, host='0.0.0.0',
            port=5001)  # with this we dont need to stop the running flask app, only need to refresh the page in the browser to load the new changes