import argparse
import json

import numpy as np

import database
from flask import Flask, render_template, request, redirect, session, flash, make_response, jsonify
from flask_login import login_user, LoginManager, logout_user, current_user
from mongoengine import *

from config import Config
import os
import logging
from src.utils import add_fields_from_data


logging.basicConfig(filename='record.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder='./static')
app.config.from_object(Config)

parser = argparse.ArgumentParser()
parser.add_argument('--config_path')
args = parser.parse_args()
with open(args.config_path) as f:
    configs = json.load(f)

connect(configs["data_reader_class"]["name"], host=f'mongodb://{"mongo-container"}:{27017}/{configs["data_reader_class"]["name"]}', port=27017)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def loader_user(_user_id):
    user = database.User.objects(_user_id=_user_id).first()
    return user
# login page
@app.route("/")
@app.route("/start_annotate/<int:experiment_id>", methods=['GET', 'POST'])
def start_annotate(experiment_id):
    # app.logger.debug(database.test_connection())
    session['exp_id'] = experiment_id
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

    return render_template('start_annotate.html')


def get_next_task_URL(exp_id, n_task):
    url = str(exp_id) + '/index_annotate/' + str(n_task)
    return url


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user();
    response = make_response(redirect('/login', code=200))
    response.headers['HX-Redirect'] = '/login'
    return response

@app.route('/api/<experiment_id>/get_next_task/', methods=['GET'])
def get_next_task(experiment_id):
    experiment = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    user = database.User.objects(_user_id=session['user_id']).first()

    experiment_tasks = list(range(0, len(experiment.tasks)))
    user_tasks_visited = [int(item.task) for item in user.tasks_visited]
    not_visited = [task for task in experiment_tasks if task not in user_tasks_visited]

    if len(not_visited) > 0:
        next_task = np.random.choice(not_visited)
    else:
        if configs["ui_display_config"]["exit_survey"] is not None:
            next_task = 'form'

    return jsonify({'next_task': str(next_task)})

@app.route("/start_annotate/<experiment_id>/index_annotate/<n_task>", methods=['GET', 'POST'])
# @login_required
def index_annotate(experiment_id, n_task):
    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(n_task)]

    task_obj = database.TaskScore.objects(_id=task_id).first()
    data_obj = database.Data.objects(_id=task_obj.data).first()
    query_obj = database.QueryRepr.objects(_id=data_obj.query).first()
    docs = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type][0].docs

    docs_obj = [database.DocRepr.objects(_id=doc_id).first() for doc_id in docs]
    doc_obj = docs_obj[int(task_obj.index)]

    doc_field_names_display = configs["ui_display_config"]["display_fields"]

    user = database.User.objects(_user_id=session['user_id']).first()
    if n_task not in [item.task for item in user.tasks_visited]:
        task_visited = database.TaskVisited(task=str(n_task), exp=str(experiment_id))
        user.tasks_visited.append(task_visited)
        user.save()

    query_title = query_obj.title
    query_text = query_obj.text

    current_url = '/start_annotate/' + str(experiment_id) + '/index_annotate/' + str(n_task) + '/'
    view_configs = configs["ui_display_config"]

    for filed in doc_field_names_display:
        if isinstance(doc_obj[filed], str):
            if '{' in doc_obj[filed] or '[' in doc_obj[filed]:
                doc_obj[filed] = eval(doc_obj[filed])

    if task_obj.setting:
        task_description = "Please pay attention to the extra information provided as it might differ between the tasks. "
        task_description = task_description + configs["ui_display_config"][
            "task_description"] + " EXTRA INFORMATION TO CONSIDER: " + task_obj.setting
    else:
        task_description = configs["ui_display_config"]["task_description"]

    return render_template('index_annotate_documents.html', doc_field_names=doc_field_names_display,
                           view_configs=view_configs,
                           data_obj=doc_obj, ranking_type=task_obj.ranking_type, query_title=query_title,
                           query_text=query_text,
                           current_url=current_url, task_description=task_description, score_range=configs["ui_display_config"]["score_range"],
                           session_id = session['user_id'])


@app.route('/store_data_annotate', methods=['POST'])
def store_data_annotate():
    data = request.get_json()
    score = str(data.get('score', []))

    doc_id = str(data.get('docId'))
    query_id = str(data.get('queryId'))
    n_task = str(data.get('nTask'))

    interaction_obj = database.InteractionScore(doc=doc_id, query=query_id,
                                                  score=score)
    user = database.User.objects(_user_id=session['user_id']).first()

    for index, item in enumerate(user.tasks_visited):
        if item.task == str(n_task):
            item.interaction_score = interaction_obj
            user.tasks_visited[index] = item
            user.save()
            break

    return "ok"


@app.route("/form/", methods=['GET', 'POST'])
# @login_required
@app.route("/form/", methods=['GET', 'POST'])
# @login_required
def form_demographic_data():
    if configs['ui_display_config']['exit_survey'] is not False:
        return render_template('form_template.html', items=configs['ui_display_config']['exit_survey'])
    else:
        return render_template('stop_experiment_template.html')


@app.route("/form_submit/", methods=['GET', 'POST'])
# @login_required
def form_submit():
    data = request.get_json()
    form_results = data.get('form_results', [])

    user = database.User.objects(_user_id=session['user_id']).first()
    add_fields_from_data(list(form_results.keys()), list(form_results.values()), user)
    user.save()

    return "ok"
       
def compute_krippendorf_kappa():
    """
        reference: https://pypi.org/project/agreement/
    """
    all_users = database.User.objects()
    users_rates_dataset = []
    for user in all_users:
        user_id = user._user_id
        app.logger.debug("user_id in the krippendorf func %s", user_id)
        # query_interaction = {}
        # temp = []
        for task_visited in user.tasks_visited:
            temp = []
            interaction_score = task_visited.interaction_score
            temp.append((interaction_score.query, interaction_score.doc))
            temp.append(user_id)
            temp.append(interaction_score.score)
            # print(len(temp))
            users_rates_dataset.append(temp)
    # print(len(users_rates_dataset))
    # app.logger.debug("users rates dataset ", users_rates_dataset)

    unique_ids = {}
    id_counter = 1

    for i in range(len(users_rates_dataset)):
        key = users_rates_dataset[i][0]  #get the unique combination of query and doc
        if key not in unique_ids:
            unique_ids[key] = f"id_{id_counter}"  #assign a new unique id
            id_counter += 1
        users_rates_dataset[i][0] = unique_ids[key] 
    for item in users_rates_dataset:
        for val in item:
            app.logger.debug("before numpy %s", str(val))
    users_rates_dataset = np.array(users_rates_dataset)
    for item in users_rates_dataset:
        for val in item:
            app.logger.debug("after numpy %s", str(val))
    app.logger.debug("users rates dataset in numpy", users_rates_dataset)
    questions_answers_table = pivot_table_frequency(users_rates_dataset[:, 0], users_rates_dataset[:, 2])
    alpha = krippendorffs_alpha(questions_answers_table)
    
    return alpha

@app.route("/stop_experiment/", methods=['GET', 'POST'])
# @login_required
def stop_experiment():
    if "attention_check" in configs:
        user = database.User.objects(_user_id=session['user_id']).first()
        experiment = database.Experiment.objects(_exp_id=str(session['exp_id'])).first()
        task = database.TaskScore.objects(query_title = configs["attention_check"]["task"]["query_title"], index = configs["attention_check"]["task"]["index"], ranking_type= configs["attention_check"]["task"]["ranking_type"]).first()
        attention_check_task = [task_visited for task_visited in user.tasks_visited if
                                task_visited.task == str(experiment.tasks.index(str(task._id)))][0]

        attention_check = attention_check_task.interaction_score.score == configs["attention_check"]["correct_answer"]
        user._attention_check = str(attention_check)
        user.save()

    return render_template('stop_experiment_template.html')


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True, host='0.0.0.0',
            port=5003) 