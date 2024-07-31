"""
MIT License

Copyright (c) 2024 Clara Rus and Gabrielle Poerwawinata

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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
    """
    Load a user from the database based on the given user ID.

    Args:
        _user_id (str): The ID of the user to load.

    Returns:
        User: The loaded user object.

    """
    user = database.User.objects(_user_id=_user_id).first()
    return user


@app.route("/")
@app.route("/start_compare_annotate/<int:experiment_id>", methods=['GET', 'POST'])
def start_compare_annotate(experiment_id):
    """
    The first function is when the user logs in to the ranking compare app.
    The ranking compares annotate app is used to select which ranking is better based on the visual investigation.
    This is different with the app_ranking_compare_annotate.

    Parameters:
    - experiment_id: The ID of the experiment.

    Returns:
    - If the user is authenticated, it redirects to the next task URL.
    - If the request method is POST, it records the user in the database, creates a new user in the database if it doesn't exist,
      creates a user session, and redirects to the next task URL.
    - If the user is not authenticated and the request method is not POST, it renders the 'start_compare.html' template.

    """
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
    """
    Redirects to the next task URL for the given experiment ID.

    Parameters:
    experiment_id (int): The ID of the experiment.

    Returns:
    response (flask.Response): The redirect response with the next task URL.
    """
    url = get_next_task_URL(experiment_id, 0)
    response = make_response(redirect(url, code=200))
    response.headers['HX-Redirect'] = url
    return response


def get_next_task_URL(exp_id, n_task):
    """Generate the URL for the next task based on the task in experiment list

    Args:
        exp_id (int): The ID of the experiment.
        n_task (int): The task number.

    Returns:
        str: The URL for the next task.
    """
    url = str(exp_id) + '/index_compare/' + str(n_task)
    return url


@app.route('/api/<experiment_id>/get_task/<direction>/<task_n>', methods=['GET'])
def get_task(experiment_id, direction, task_n):
    """
    Retrieves the next or previous task based on the given experiment ID, direction, and task number.

    Args:
        experiment_id (str): The ID of the experiment.
        direction (str): The direction to navigate the tasks. Can be either 'next' or 'previous'.
        task_n (int): The current task number.

    Returns:
        dict: A JSON response containing the next task number.

    """
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
    """The main page of compare rankings app. Defines all the data required for the annotate 2 rankings app.

    Args:
        experiment_id (str): The ID of the experiment.
        n_task (int): The index of the task.

    Returns:
        render_template: The rendered HTML template for the index_ranking_compare_template.

    """
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
