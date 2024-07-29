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


# login page
@login_manager.user_loader
def loader_user(_user_id):
    user = database.User.objects(_user_id=_user_id).first()
    return user
@app.route("/")
@app.route("/start_compare_annotate/<int:experiment_id>", methods=['GET', 'POST'])
def start_compare_annotate(experiment_id):
    """
    The first function is when the user logs in to the ranking compare annotate app. 
    The ranking compares annotate app, which is used to select which ranking is better based on the visual investigation. In this app, the user has to select one of the best-displayed rankings.  

    Parameters:
    - experiment_id: The ID of the experiment.

    Returns:
    - If the user is authenticated, it redirects to the next task URL.
    - If the request method is POST, it records the user in the database, creates a new user in the database if it doesn't exist, creates a user session, and redirects to the next task URL.
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
    """
    Logs out the user and redirects to the login page.

    Returns:
        A Flask response object with a redirect to the login page.
    """
    logout_user()
    response = make_response(redirect('/login', code=200))
    response.headers['HX-Redirect'] = '/login'
    return response


def get_next_task_URL(exp_id, n_task):
    """Generate the URL for the next task based on the task in experiment list
    
    Args:
        exp_id (int): The ID of the experiment.
        n_task (int): The task number.
    
    Returns:
        str: The URL for the next task.
    """
    url = str(exp_id) + '/index_compare_annotate/' + str(n_task)
    return url


@app.route('/api/<experiment_id>/get_next_task_annotate_compare/', methods=['GET'])
def get_next_task_annotate_compare(experiment_id):
    """Get the next task to be assessed by the annotator based on the experiment list.

    Args:
        experiment_id (str): The ID of the experiment.

    Returns:
        dict: A JSON response containing the next task to be assessed by the annotator.
    """
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


@app.route("/form/", methods=['GET', 'POST'])
# @login_required
def form_demographic_data():
    """
    Renders a template based on the exit survey configuration.

    If the 'exit_survey' configuration is not set to False, it renders the 'form_template.html' template
    with the items specified in the 'exit_survey' configuration. Otherwise, it renders the 'stop_experiment_template.html' template.

    Returns:
        A rendered template based on the exit survey configuration.
    """
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

@app.route('/store_data_compare_ranking', methods=['POST'])
def store_data_compare_ranking_ranking():
    """Store the researcher ranking selection.

    This function is responsible for storing the researcher ranking selection made by the user. It retrieves the ranking
    types, the task number, and the selected ranking from the request's JSON data. It then creates an instance of the
    InteractionCompare class with the provided ranking types and selected ranking.

    The function retrieves the user object based on the session's user ID and updates the interaction_compare attribute
    of the corresponding task in the user's tasks_visited list. Finally, it saves the updated user object and returns
    "ok" to indicate successful storage.

    Returns:
        str: A string indicating the success of the storage operation ("ok").
    """
    data = request.get_json()
    ranking_type_1 = data.get('ranking_type_1')
    ranking_type_2 = data.get('ranking_type_2')
    n_task = data.get('nTask')
    selected_ranking = data.get('selected_ranking')

    interaction_obj = database.InteractionCompare(ranking_type_1=ranking_type_1, ranking_type_2=ranking_type_2,
                                                     selected_ranking=selected_ranking)

    user = database.User.objects(_user_id=session['user_id']).first()
    for index, item in enumerate(user.tasks_visited):
        if item.task == str(n_task):
            item.interaction_compare = interaction_obj
            user.tasks_visited[index] = item
            user.save()
            break

    return "ok"
@app.route("/start_compare_annotate/<experiment_id>/index_compare_annotate/<n_task>", methods=['GET', 'POST'])
def index_compare_annotate(experiment_id, n_task):
    """Defines all the data required for the annotate 2 rankings app.

    Args:
        experiment_id (str): The ID of the experiment.
        n_task (int): The index of the task.

    Returns:
        render_template: The rendered template for the annotate 2 rankings app.
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

    current_url = '/start_compare_annotate/' + str(experiment_id) + '/index_compare_annotate/' + str(n_task) + '/'

    user = database.User.objects(_user_id=session['user_id']).first()
    if n_task not in [item.task for item in user.tasks_visited]:
        task_visited = database.TaskVisited(task=str(n_task), exp=str(experiment_id))
        user.tasks_visited.append(task_visited)
        user.save()

    view_configs = configs["ui_display_config"]

    if task_obj.setting:
        task_description = "Please pay attention to the extra information provided as it might differ between the tasks. "
        task_description = task_description + configs["ui_display_config"][
            "task_description"] + " EXTRA INFORMATION TO CONSIDER: " + task_obj.setting
    else:
        task_description = configs["ui_display_config"]["task_description"]

    return render_template('index_ranking_compare_template.html', doc_field_names=doc_field_names_display,
                           view_configs=view_configs,
                           doc_data_objects_1=docs_obj_1, doc_data_objects_2=docs_obj_2,
                           ranking_type_1=task_obj.ranking_type_1, ranking_type_2=task_obj.ranking_type_2,
                           query_title=query_title, query_text=query_text, current_url=current_url, task_description=task_description)



@app.route("/stop_experiment/", methods=['GET', 'POST'])
# @login_required
def stop_experiment():
    return render_template('stop_experiment_template.html')


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True, host='0.0.0.0',
            port=5002)  
