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
from src.utils import  add_fields_from_data

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
    
connect(configs["data_reader_class"]["name"], host='mongo', port=27017)
#connect(configs["data_reader_class"], host='0.0.0.0', port=27017)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def loader_user(_user_id):
    user = database.User.objects(_user_id=_user_id).first()
    return user


# login page
@app.route("/")
@app.route("/start_ranking/<int:experiment_id>", methods=['GET', 'POST'])
def start_ranking(experiment_id):
    """First function when the user logged in into the ranking app. 
    In this ranking app, the user will be presented by list of items, where they have to choose the top-3 items based on a given query. 

    Parameters:
    experiment_id (int): The ID of the experiment.

    Returns:
    flask.Response or flask.render_template: The response object or the rendered template for the start ranking page.
    """

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

    return render_template('start_ranking.html')


def get_next_task_URL(exp_id, n_task):
    url = str(exp_id) + '/index_ranking/' + str(n_task) + '/view'
    return url


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


@app.route("/start_ranking/<experiment_id>/index_ranking/<n_task>/<doc_id>", methods=['GET', 'POST'])
# @login_required
def index_ranking(experiment_id, n_task, doc_id):
    """
    Renders the index ranking template for a given experiment, task, and document.

    Args:
        experiment_id (str): The ID of the experiment.
        n_task (int): The index of the task.
        doc_id (str): The ID of the document.

    Returns:
        str: The rendered HTML template for the index ranking page.
    """
    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(n_task)]

    task_obj = database.Task.objects(_id=task_id).first()
    data_obj = database.Data.objects(_id=task_obj.data).first()
    query_obj = database.QueryRepr.objects(_id=data_obj.query).first()
    docs = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type][0].docs
    docs_obj = [database.DocRepr.objects(_id=doc_id).first() for doc_id in docs]
    doc_field_names_display = configs["ui_display_config"]["display_fields"]

    if configs["ui_display_config"]["view_button"]:
        doc_field_names_view = configs["ui_display_config"]["view_fields"]
    else:
        doc_field_names_view = []

    if task_obj.setting:
        task_description = "Please pay attention to the extra information provided as it might differ between the tasks. "
        task_description = task_description + configs["ui_display_config"][
            "task_description"] + " EXTRA INFORMATION TO CONSIDER: " + task_obj.setting
    else:
        task_description = configs["ui_display_config"]["task_description"]

    if doc_id != 'view':
        doc_obj = docs_obj[int(doc_id) - 1]

        return render_template('doc_ranking_view_information_template.html', doc_obj=doc_obj,
                               field_names=doc_field_names_view, doc_index=doc_id, task_description=task_description)

    user = database.User.objects(_user_id=session['user_id']).first()
    if n_task not in [item.task for item in user.tasks_visited]:
        task_visited = database.TaskVisited(task=str(n_task), exp=str(experiment_id))
        user.tasks_visited.append(task_visited)
        user.save()

    query_title = query_obj.title
    query_text = query_obj.text

    current_url = '/start_ranking/' + str(experiment_id) + '/index_ranking/' + str(n_task) + '/'
    view = len(doc_field_names_view) > 0
    if not view:
        configs["ui_display_config"]["view"] = False

    view_configs = configs["ui_display_config"]
    return render_template('index_ranking_template.html', doc_field_names=doc_field_names_display,
                           view_configs=view_configs,
                           doc_data_objects=docs_obj, ranking_type=task_obj.ranking_type,  query_title=query_title,
                           query_text=query_text,
                           current_url=current_url, task_description=task_description, session_id = session['user_id'])



@app.route('/api/<experiment_id>/get_next_task/', methods=['GET'])
def get_next_task(experiment_id):
    """Get the next task based on the experiment list. The task list should be defined in the experiment list. 
    
    Args:
        experiment_id (str): The ID of the experiment.
        
    Returns:
        dict: A dictionary containing the next task.
            - 'next_task' (str): The ID of the next task.
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


@app.route('/store_data_ranking', methods=['POST'])
def store_data_ranking():
    """
    Stores the ranking data received from the client.

    This function retrieves the ranking data from the request's JSON payload and stores it in the database.
    The ranking data includes the number of tasks, interactions, and order checkbox values.

    Returns:
        str: A string indicating the success of the data storage process.
    """
    data = request.get_json()
    n_task = data.get('nTask')
    interactions = data.get('interactions')
    orderCheckbox = data.get('orderCheckBox', [])

    all_interactions = []
    for doc_id in interactions.keys():
        interactions_document = database.Interaction(doc_id=doc_id, n_views=str(interactions[doc_id]['n_views']),
                                                     timestamps=interactions[doc_id]['timestamps'],
                                                     shortlisted=str(interactions[doc_id]['shortlisted']))
        all_interactions.append(interactions_document)

    user = database.User.objects(_user_id=session['user_id']).first()
    for index, item in enumerate(user.tasks_visited):
        if item.task == str(n_task):
            item.interactions = all_interactions
            item.order_checkbox = orderCheckbox
            user.tasks_visited[index] = item
            user.save()

    return "ok"


@app.route("/form/", methods=['GET', 'POST'])
# @login_required
def form_demographic_data():
    """
    Renders a template based on the exit survey configuration.

    If the 'exit_survey' configuration in 'ui_display_config' is not False,
    it renders the 'form_template.html' template with the items from the
    'exit_survey' configuration. Otherwise, it renders the
    'stop_experiment_template.html' template.

    Returns:
        The rendered template.
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


@app.route("/stop_experiment/", methods=['GET', 'POST'])
# @login_required
def stop_experiment():
    """This function is called when the final task in the ranking task is completed.
    
    It performs the following actions:
    1. Checks if there is an attention check task defined in the configs.
    2. Retrieves the user and experiment objects from the database.
    3. Retrieves the attention check task from the database based on the query title and ranking type defined in the configs.
    4. Retrieves the attention check task visited by the user.
    5. Retrieves the correct answers for the attention check task from the database.
    6. Compares the user's selected answers with the correct answers to determine if the attention check is passed or failed.
    7. Updates the user's attention check status in the database.
    8. Renders the 'stop_experiment_template.html' template.
    
    Returns:
        The rendered template 'stop_experiment_template.html'.
    """
    if "attention_check" in configs:
        user = database.User.objects(_user_id=session['user_id']).first()
        experiment = database.Experiment.objects(_exp_id=str(session['exp_id'])).first()
        task = database.Task.objects(query_title=configs["attention_check"]["task"]["query_title"], ranking_type=configs["attention_check"]["task"]["ranking_type"]).first()
        attention_check_task = [task_visited for task_visited in user.tasks_visited if
                                task_visited.task == str(experiment.tasks.index(str(task._id)))][0]
        correct_answers = []
        for doc_id in configs["attention_check"]["correct_answer"]:
            filter = {configs["data_reader_class"]["docID"]: doc_id}
            correct_answer = database.DocRepr.objects.filter(**filter).first()
            correct_answers.append(str(correct_answer._id))

        attention_check = sorted(attention_check_task.order_checkbox) == sorted(correct_answers)
        user._attention_check = str(attention_check)
        user.save()

    return render_template('stop_experiment_template.html')



if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0',
            port=5000)  # with this we dont need to stop the running flask app, only need to refresh the page in the browser to load the new changes
