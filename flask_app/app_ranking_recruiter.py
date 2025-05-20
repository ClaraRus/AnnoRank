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

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

import argparse
import json

import numpy as np
import os
import logging

import database
from flask import Flask, render_template, request, redirect, session, flash, make_response, jsonify, abort, send_from_directory, url_for
from flask_login import login_user, LoginManager, logout_user, current_user
from mongoengine import *

from utils.utils import add_fields_from_data
from config import Config

import ast
import math

logging.basicConfig(filename='../record.log', level=logging.DEBUG)
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
# connect(configs["data_reader_class"], host='0.0.0.0', port=27017)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def loader_user(_user_id):
    user = database.User.objects(_user_id=_user_id).first()
    return user


# login page
@app.route("/")
@app.route("/start_ranking_recruiter/<int:experiment_id>", methods=['GET', 'POST'])
def start_ranking(experiment_id):
    """Renders the Log-in page for the Interaction Annotate UI.

    Args:
        experiment_id (int): The ID of the experiment.

    Returns:
        flask.Response or flask.render_template: The response object or the rendered template for the start ranking page.

    Notes:
        This function is responsible for handling the initial steps when a user logs in to the Interaction Annotate UI.
        If the user is authenticated, it sets the session variables and redirects to the next task URL.
        If the request method is POST, it records the user in the database and creates a new user if necessary.
        Finally, it renders the 'start_ranking.html' template.

    """

    session['exp_id'] = experiment_id

    if current_user.is_authenticated:
        session['user_id'] = current_user._user_id

        try:
            next_task = get_next_task(experiment_id).get_json()
        except:
            response = make_response(redirect("/404/Failed get next task!", code=200))
            response.headers['HX-Redirect'] = "/404/Failed get next task!"
            return response

        if next_task['next_task'] == 'form':
            url = '/form/'
        elif next_task['next_task'] == 'stop_experiment':
            url = '/stop_experiment/'
        else:
            url = str(experiment_id) + '/index_ranking/' + str(next_task['next_task']) + "/view"

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

            try:
                next_task = get_next_task(experiment_id).get_json()
            except:
                response = make_response(redirect("/404/Failed get next task!", code=200))
                response.headers['HX-Redirect'] = "/404/Failed get next task!"
                return response

            # if next_task['next_task'] == 'form':
            #     url = '/form/'
            # elif next_task['next_task'] == 'stop_experiment':
            #     url = '/stop_experiment/'
            # else:
            #     url = str(experiment_id) + '/index_ranking/' + str(next_task['next_task']) + "/view"

            # response = make_response(redirect(url, code=200))
            # response.headers['HX-Redirect'] = url
            # return response

            if next_task['next_task'] == 'form':
                url = '/form/'
            elif next_task['next_task'] == 'stop_experiment':
                url = '/stop_experiment/'
            else:
                url = url_for('index_ranking', experiment_id=experiment_id, n_task=next_task['next_task'], doc_id="view")
                #url = f"{experiment_id}/index_ranking/{next_task['next_task']}/view"

            # Store target for after consent
            session['next_url'] = url

            # Redirect to consent form instead
            consent_url = url_for('consent_form', experiment_id=experiment_id)
            response = make_response(redirect(consent_url, code=200))
            response.headers['HX-Redirect'] = consent_url
            return response

        else:
            flash('Invalid user_id', 'danger')

    return render_template('start_ranking_recruiter.html')

#added
@app.route("/consent/<int:experiment_id>", methods=['GET', 'POST'])
def consent_form(experiment_id):
    if request.method == 'POST':
        # Redirect to instructions page, NOT directly to tasks
        instructions_url = url_for('instructions', experiment_id=experiment_id)
        return redirect(instructions_url)

    return render_template('consent_form_template_recruiter.html', experiment_id=experiment_id)


#added
@app.route("/instructions/<int:experiment_id>", methods=['GET', 'POST'])
def instructions(experiment_id):
    if request.method == 'POST':
        # After instructions are acknowledged, redirect to next task
        next_url = session.get('next_url')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('/')  # fallback

    return render_template('task_description_shortlist_page_template_recruiter.html', experiment_id=experiment_id)





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


@app.route('/api/<experiment_id>/get_next_task/', methods=['GET'])
def get_next_task(experiment_id):
    """Get the next task to be assessed by the annotator based on the experiment list.

    Args:
        experiment_id (str): The ID of the experiment.

    Returns:
        dict: A JSON response containing the next task to be assessed.
            The response has the following format:
            {
                'next_task': str
            }
            If there are no more tasks to be assessed, the 'next_task' value will be 'form' or 'stop_experiment'.
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
        else:
            next_task = 'stop_experiment'

    return jsonify({'next_task': str(next_task)})


@app.route("/start_ranking_recruiter/<experiment_id>/index_ranking/<n_task>/<doc_id>", methods=['GET', 'POST'])
# @login_required
def index_ranking(experiment_id, n_task, doc_id):
    """
    Renders Interaction Annotate UI.

    Args:
        experiment_id (str): The ID of the experiment.
        n_task (int): The index of the task.
        doc_id (str): The ID of the document.
        Default is set to 'view'. When a user clikcs the view button it will be set to the ID of the document.

    Returns:
        str: The rendered HTML template for the index ranking page.
    """
    try:
        exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
        task_id = exp_obj.tasks[int(n_task)]

        task_obj = database.Task.objects(_id=task_id).first()
        data_obj = database.Data.objects(_id=task_obj.data).first()
        query_obj = database.QueryRepr.objects(_id=data_obj.query).first()
    except:
        response = make_response(redirect(f"/404/Experiment type is not for app_ranking!", code=200))
        response.headers['HX-Redirect'] = f"/404/Experiment type is not for app_ranking!"
        return response

    try:
        docs = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type][0].docs
    except:
        response = make_response(redirect(f"/404/No document with the ranking type!", code=200))
        response.headers['HX-Redirect'] = f"/404/No document with the ranking type!"
        return response

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

    # all_columns = set()
    # for doc in docs_obj:
    #     all_columns.update(doc._data.keys())
    normalized_field_names = [name.replace('_display', '') for name in doc_field_names_display]


    # get factual data
    factual_fields = configs["ui_display_config"]["factual_fields"]




    if doc_id != 'view':
        doc_obj = docs_obj[int(doc_id) - 1]

        factual_raw = getattr(doc_obj, "factuals", None)
        factual_list = []

        if factual_raw is None or (isinstance(factual_raw, float) and math.isnan(factual_raw)):
            pass  # Leave list empty
        elif isinstance(factual_raw, str):
            try:
                factual_list = ast.literal_eval(factual_raw)
            except Exception:
                factual_list = []
        elif isinstance(factual_raw, list):
            factual_list = factual_raw

        # Extract fields like education_factual, etc.
        if factual_list:
            flat_factuals = factual_list[0]
            for key in factual_fields:
                value = flat_factuals.get(key, '')
                setattr(doc_obj, key + "_factual", value)
        else:
            for key in factual_fields:
                setattr(doc_obj, key + "_factual", '')
        
        field_names = [f + "_factual" for f in factual_fields]


        return render_template('doc_ranking_view_information_template_recruiter.html', doc_obj=doc_obj,
                               field_names=field_names, doc_index=doc_id, task_description=task_description, all_columns=normalized_field_names)

    user = database.User.objects(_user_id=session['user_id']).first()
    if n_task not in [item.task for item in user.tasks_visited]:
        task_visited = database.TaskVisited(task=str(n_task), exp=str(experiment_id))
        user.tasks_visited.append(task_visited)
        user.save()

    query_title = query_obj.title
    query_text = query_obj.text

    current_url = '/start_ranking_recruiter/' + str(experiment_id) + '/index_ranking/' + str(n_task) + '/'
    view = len(doc_field_names_view) > 0
    if not view:
        configs["ui_display_config"]["view"] = False

    view_configs = configs["ui_display_config"]
    return render_template('index_ranking_template_recruiter.html', doc_field_names=doc_field_names_display,
                           view_configs=view_configs,
                           doc_data_objects=docs_obj, ranking_type=task_obj.ranking_type, query_title=query_title,
                           query_text=query_text,
                           current_url=current_url, task_description=task_description, session_id=session['user_id'])

#added
@app.route('/get_doc_detail/<doc_id>', methods=['GET'])
def get_doc_detail(doc_id):
    doc_obj = database.DocRepr.objects(_id=doc_id).first()
    if not doc_obj:
        return "Document not found", 404

    field_names = configs["ui_display_config"].get("detail_fields", [])
    return render_template(
        'doc_ranking_view_plot_and_discription_template_recruiter.html',
        doc_obj=doc_obj,
        field_names=field_names
    )

#added
@app.route('/customer_service_images/<path:filename>')
def customer_service_images(filename):
    image_dir = os.path.abspath(
        os.path.join(app.root_path, '..', 'dataset', 'cvs', 'data', 'customer_service_representative')
    )

    # Optional: restrict file types
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        abort(403)

    return send_from_directory(image_dir, filename)





@app.route('/store_data_ranking', methods=['POST'])
def store_data_ranking():
    """
    Stores the annotation data received from the user to the MongoDB database.

    Returns:
        str: A string indicating the success of the operation.
    """
    data = request.get_json()
    n_task = data.get('nTask')
    interactions = data.get('interactions')
    orderCheckbox = data.get('orderCheckBox', [])

    all_interactions = []
    for doc_id, info in interactions.items():
        interactions_document = database.Interaction(
            doc_id=doc_id,
            view_n=str(info.get('view_n', 0)),
            detail_n=str(info.get('detail_n', 0)),
            view_timestamps=info.get('view_timestamps', []),
            detail_timestamps=info.get('detail_timestamps', []),
            shortlisted=str(info.get('shortlisted', 'false'))
        )
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
    Renders the 'form_template.html' template
    with the items specified in the 'exit_survey' configuration.

    Returns:
        The rendered template.
    """
    return render_template('form_template.html', items=configs['ui_display_config']['exit_survey'])


@app.route("/form_submit/", methods=['GET', 'POST'])
# @login_required
def form_submit():
    """
    Stores the data collected in the form to the MongoDB database.

    Returns:
        str: A string indicating the success of the operation.
    """
    data = request.get_json()
    form_results = data.get('form_results', [])

    user = database.User.objects(_user_id=session['user_id']).first()
    add_fields_from_data(list(form_results.keys()), list(form_results.values()), user)
    user.save()

    return "ok"


@app.route("/stop_experiment/", methods=['GET', 'POST'])
# @login_required
def stop_experiment():
    """
    Stops the experiment and performs a quality check on the annotator's responses.

    This function is called when the app reaches the last experiment task.
    It checks whether the annotator failed the attention check task.

    Returns:
        A rendered template for the stop_experiment_template.html.
    """

    if "attention_check" in configs:
        user = database.User.objects(_user_id=session['user_id']).first()
        experiment = database.Experiment.objects(_exp_id=str(session['exp_id'])).first()
        task = database.Task.objects(query_title=configs["attention_check"]["task"]["query_title"],
                                     ranking_type=configs["attention_check"]["task"]["ranking_type"]).first()
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


@app.route("/404/<error>", methods=['GET', 'POST'])
# @login_required
def error_handling(error):
    return render_template('404.html', error=error)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0',
            port=5004)  # with this we dont need to stop the running flask app, only need to refresh the page in the browser to load the new changes
