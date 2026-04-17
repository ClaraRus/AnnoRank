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
import math

sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

import argparse
import json
import random

import numpy as np
import os
import logging
import ast

import database
from flask import Flask, render_template, request, redirect, session, flash, make_response, jsonify, abort, \
    send_from_directory, url_for
from flask_login import login_user, LoginManager, logout_user, current_user
from mongoengine import *
from config import Config

logging.basicConfig(filename='../record.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder='./static')
app.config.from_object(Config)

parser = argparse.ArgumentParser()
parser.add_argument('--config_path')
parser.add_argument('--port', type=int, default=5005)  # Add this line

args = parser.parse_args()

if os.path.exists(args.config_path):
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
@app.route("/start_ranking_XAI/<int:experiment_id>", methods=['GET', 'POST'])
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

        if len(current_user.tasks_visited) == 0:
            # Redirect to consent form instead
            consent_url = url_for('consent_form', experiment_id=experiment_id)
            response = make_response(redirect(consent_url, code=200))
            response.headers['HX-Redirect'] = consent_url
        else:
            instructions_url = url_for('instructions', experiment_id=experiment_id)
            response = make_response(redirect(instructions_url, code=200))
            response.headers['HX-Redirect'] = instructions_url
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

            if len(user.tasks_visited) == 0:
                # Redirect to consent form instead
                consent_url = url_for('consent_form', experiment_id=experiment_id)
                response = make_response(redirect(consent_url, code=200))
                response.headers['HX-Redirect'] = consent_url
            else:
                instructions_url = url_for('instructions', experiment_id=experiment_id)
                response = make_response(redirect(instructions_url, code=200))
                response.headers['HX-Redirect'] = instructions_url
            return response

        else:
            flash('Invalid user_id', 'danger')

    return render_template('start_ranking.html', experiment_id=experiment_id)


@app.route("/consent/<int:experiment_id>", methods=['GET', 'POST'])
def consent_form(experiment_id):
    if request.method == 'POST':
        url = url_for('instructions', experiment_id=experiment_id)
        return redirect(url)

    return render_template('consent_form_template.html', session_id=session['user_id'], experiment_id=experiment_id)


#added
@app.route("/instructions/<int:experiment_id>", methods=['GET', 'POST'])
def instructions(experiment_id):
    next_task = get_next_task(experiment_id).get_json()['next_task']

    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(next_task)]
    task_obj = database.Task.objects(id=task_id).first()

    if request.method == 'POST':

        if task_obj.ranking_type == "form":
            next_url = url_for('questionnaire', experiment_id=experiment_id, n_task=next_task)
        else:
            next_url = url_for('index_ranking', experiment_id=experiment_id, n_task=next_task, doc_id="view")

        return redirect(next_url)

    task_description = get_task_description(task_obj)
    return render_template('task_description_page.html', session_id=session['user_id'], experiment_id=experiment_id,
                           task_description=task_description,
                           instructions_timer=configs["ui_display_config"]["instructions_timer"])


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


# Updated get_next_task function
@app.route('/api/<experiment_id>/get_next_task/', methods=['GET'])
def get_next_task(experiment_id):
    """Get the next task to be assessed by the annotator based on the experiment list defined in the JSON.

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

    if "attention_check" in configs:
        if user._attention_check == "":
            user._attention_check = str(0)
            user.save()
        if "limit" in configs["attention_check"]:
            if int(user._attention_check) >= configs["attention_check"]["limit"]:
                next_task = 'stop_experiment'
                return jsonify({'next_task': str(next_task)})

    # Convert visited tasks to a set for more efficient lookups
    user_tasks_visited_ids = {item.task for item in user.tasks_visited}

    # Iterate through tasks in the order defined in the experiment's 'tasks' JSON array
    for idx, task_obj_id in enumerate(experiment.tasks):
        # Check if the task index (idx) has not been visited by the user yet
        if str(idx) not in user_tasks_visited_ids:
            # We found the next unvisited task in the JSON order
            return jsonify({'next_task': str(idx)})

    # If all tasks defined in the 'tasks' array of the JSON have been visited
    if configs["ui_display_config"]["exit_survey"] is not None:
        next_task = 'form'
    else:
        next_task = 'stop_experiment'

    return jsonify({'next_task': str(next_task)})


def get_task_description(task_obj):
    if task_obj:
        if task_obj.show_xai != False:
            base_description = configs["ui_display_config"]["task_description_xai"]  # For XAI
        else:
            base_description = configs["ui_display_config"]["task_description"]  # For No-XAI
    else:
        base_description = ""

    # Add extra information specific to the task, if available
    if task_obj is not None and task_obj.setting:
        return (
                "Please pay attention to the extra information provided as it might differ between the tasks. "
                + base_description
                + " EXTRA INFORMATION TO CONSIDER: "
                + task_obj.setting
        )
    return base_description


def get_xai_data(doc_obj, ranking_type, type="factual"):
    if type == "image_text":
        for xai_type in ["image", "text"]:
            xai_raw = getattr(doc_obj, f'{xai_type}_xai', None)
            xai_list = []

            if xai_raw is None or (isinstance(xai_raw, float) and math.isnan(xai_raw)):
                pass
            elif isinstance(xai_raw, str):
                try:
                    xai_list = ast.literal_eval(xai_raw)
                except Exception:
                    xai_list = []
            elif isinstance(xai_raw, list):
                xai_list = xai_raw

            xai_data_list = [xai for xai in xai_list if xai.get("ranking_type") == ranking_type]

            if xai_data_list:
                setattr(doc_obj, f'{xai_type}_xai', xai_data_list[0])
            else:
                setattr(doc_obj, f'{xai_type}_xai', {})

        return None, doc_obj

    xai_raw = getattr(doc_obj, f'{type}_xai', None)
    xai_list = []

    if xai_raw is None or (isinstance(xai_raw, float) and math.isnan(xai_raw)):
        pass
    elif isinstance(xai_raw, str):
        try:
            xai_list = ast.literal_eval(xai_raw)
        except Exception:
            xai_list = []
    elif isinstance(xai_raw, list):
        xai_list = xai_raw

    xai_data_list = [xai for xai in xai_list if xai.get("ranking_type") == ranking_type]
    user = database.User.objects(_user_id=session['user_id']).first()
    user["debug"].extend(xai_data_list)
    user.save()

    if not xai_data_list:
        if type == "counterfactual":
            doc_obj.counterfactuals = {}
        elif type == "factual":
            return [], doc_obj
        elif type == "image":
            doc_obj.image_xai = {}
        elif type == "text":
            doc_obj.text_xai = {}
        return None, doc_obj

    if type == "counterfactual":
        doc_obj.counterfactuals = xai_data_list[0]
        return None, doc_obj

    elif type == "factual":
        xai_data = xai_data_list[0]
        xai_fields = xai_data.get("data", {}).keys()

        if xai_data.get("data"):
            for key in xai_fields:
                value = xai_data["data"].get(key, '')
                setattr(doc_obj, key + f"_{type}", value)
        else:
            for key in xai_data:
                setattr(doc_obj, key + f"_{type}", '')

        field_names = [f + f"_{type}" for f in xai_fields]

        setattr(doc_obj, f"{type}_image", xai_data.get(f"{type}_image", ""))
        setattr(doc_obj, f"{type}_text", xai_data.get(f"{type}_text", ""))

        return field_names, doc_obj

    elif type == "image":
        doc_obj.image_xai = xai_data_list[0]
        return None, doc_obj

    elif type == "text":
        doc_obj.text_xai = xai_data_list[0]
        return None, doc_obj

    return None, doc_obj


@app.route("/start_ranking_XAI/<experiment_id>/index_ranking/<n_task>/<doc_id>",
           methods=['GET', 'POST'])
#@login_required
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
        task_obj = database.Task.objects(id=task_id).first()
        data_obj = database.Data.objects(_id=task_obj.data).first()
        query_obj = database.QueryRepr.objects(_id=data_obj.query).first()
    except Exception as e:
        logger.error(f"Error loading task data in index_ranking: {e}")
        response = make_response(redirect(f"/404/Failed to load task data: {e}", code=200))
        response.headers['HX-Redirect'] = f"/404/Failed to load task data: {e}"
        return response

    try:
        docs = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type][0].docs
    except:
        response = make_response(redirect(f"/404/No document with the ranking type!", code=200))
        response.headers['HX-Redirect'] = f"/404/No document with the ranking type!"
        return response

    docs_obj = [database.DocRepr.objects(_id=doc_id).first() for doc_id in docs]
    doc_field_names_display = configs["ui_display_config"]["display_fields"]

    if "cand_idx" in task_obj:
        docs_obj = [docs_obj[int(task_obj.cand_idx)]]

    # add display of score column
    if 'score_column' in task_obj:
        if task_obj.score_column not in doc_field_names_display:
            if len(doc_field_names_display) == configs["ui_display_config"]["display_fields"]:
                doc_field_names_display.append(task_obj.score_column)
            else:
                doc_field_names_display[-1] = task_obj.score_column

    if task_obj.show_xai != False:
        configs["ui_display_config"]["view_button"] = True
    else:
        configs["ui_display_config"]["view_button"] = False

    if configs["ui_display_config"]["view_button"]:
        doc_field_names_view = configs["ui_display_config"]["view_fields"]
    else:
        doc_field_names_view = []

    task_description = get_task_description(task_obj)

    normalized_field_names = [name.replace('_display', '') for name in doc_field_names_display]

    # get  XAI data
    if doc_id != 'view':
        doc_obj = docs_obj[int(doc_id) - 1]

        field_names, doc_obj = get_xai_data(doc_obj, task_obj.ranking_type, type=task_obj.show_xai)

        return render_template('xai_section_template.html', session_id=session['user_id'],
                               doc_obj=doc_obj, n_task=n_task,
                               field_names=field_names, doc_index=doc_id, task_description=task_description,
                               all_columns=normalized_field_names, ranking_type=task_obj.ranking_type,
                               shortlist_button=configs["ui_display_config"]["shortlist_button"],
                               show_xai=task_obj.show_xai, experiment_id=experiment_id,
                               view_configs=configs["ui_display_config"])

    user = database.User.objects(_user_id=session['user_id']).first()
    if n_task not in [item.task for item in user.tasks_visited]:
        task_visited = database.TaskVisited(task=str(n_task), exp=str(experiment_id))
        user.tasks_visited.append(task_visited)
        user.save()

    query_title = query_obj.title
    query_text = query_obj.text

    current_url = url_for('index_ranking', experiment_id=experiment_id, n_task=n_task, doc_id="")

    view = len(doc_field_names_view) > 0
    if not view:
        configs["ui_display_config"]["view"] = False

    view_configs = configs["ui_display_config"]
    return render_template('index_ranking_template_XAI.html', doc_field_names=doc_field_names_display,
                           view_configs=view_configs, experiment_id=experiment_id, n_task=n_task,
                           doc_data_objects=docs_obj, ranking_type=task_obj.ranking_type, query_title=query_title,
                           query_text=query_text,
                           current_url=current_url, task_description=task_description, session_id=session['user_id'])




@app.route('/images/<path:filename>')
def images(filename):
    if filename is not None:
        # Optional: restrict file types
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            abort(403)

        data_name = configs["data_reader_class"]["name"]

        image_dir = os.path.abspath(
            os.path.join(app.root_path, '..', 'dataset', data_name, 'data')
        )
        return send_from_directory(image_dir, filename)
    return "No filename!"


@app.route('/image_text_explanation/<experiment_id>/<n_task>/<doc_id>', methods=['GET', 'POST'])
def image_text_explanation(experiment_id, n_task, doc_id):
    doc_obj = database.DocRepr.objects(_id=doc_id).first()

    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(n_task)]
    task_obj = database.Task.objects(id=task_id).first()

    _, doc_obj = get_xai_data(doc_obj, task_obj.ranking_type, type="image")

    return render_template('doc_ranking_view_information_text_image_XAI_template.html',
                           doc_obj=doc_obj,
                           type="image_text")


@app.route('/start_ranking/<experiment_id>/index_ranking/<n_task>/<doc_id>/text_explanation',
           methods=['GET'])
def text_explanation(experiment_id, n_task, doc_id):
    doc_obj = database.DocRepr.objects(_id=doc_id).first()

    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(n_task)]
    task_obj = database.Task.objects(id=task_id).first()

    _, doc_obj = get_xai_data(doc_obj, task_obj.ranking_type, type="text")

    return render_template('doc_ranking_view_information_text_image_XAI_template.html',
                           session_id=session['user_id'], doc_obj=doc_obj, type="text")


@app.route('/start_ranking/<experiment_id>/index_ranking/<n_task>/<doc_id>/image_explanation',
           methods=['GET'])
def image_explanation(experiment_id, n_task, doc_id):
    doc_obj = database.DocRepr.objects(_id=doc_id).first()

    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(n_task)]
    task_obj = database.Task.objects(id=task_id).first()

    _, doc_obj = get_xai_data(doc_obj, task_obj.ranking_type, type="image")

    return render_template('doc_ranking_view_information_text_image_XAI_template.html',
                           session_id=session['user_id'], doc_obj=doc_obj, type="image")


@app.route('/start_ranking/<experiment_id>/index_ranking/<n_task>/<doc_id>/cf_explanation',
           methods=['GET'])
def counterfactual_explanation(experiment_id, n_task, doc_id):
    doc_obj = database.DocRepr.objects(_id=doc_id).first()

    doc_field_names_display = configs["ui_display_config"]["display_fields"][:]

    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(n_task)]
    task_obj = database.Task.objects(id=task_id).first()

    _, doc_obj = get_xai_data(doc_obj, task_obj.ranking_type, type="counterfactual")

    return render_template('doc_ranking_view_information_counterfactual_XAI_template.html',
                           session_id=session['user_id'], doc_obj=doc_obj, field_names=doc_field_names_display,
                           doc_index=doc_id)


@app.route('/start_ranking_XAI/<experiment_id>/index_ranking/<n_task>/<doc_id>/f_explanation',
           methods=['GET'])
def factual_explanation(experiment_id, n_task, doc_id):
    doc_obj = database.DocRepr.objects(_id=doc_id).first()

    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(n_task)]
    task_obj = database.Task.objects(id=task_id).first()

    field_names, doc_obj = get_xai_data(doc_obj, task_obj.ranking_type, type="factual")
    doc_field_names_display = configs["ui_display_config"]["display_fields"]
    normalized_field_names = [name.replace('_display', '') for name in doc_field_names_display]

    return render_template('doc_ranking_view_information_factual_XAI_template.html',
                           session_id=session['user_id'],
                           doc_obj=doc_obj,
                           field_names=field_names, doc_index=doc_id,
                           all_columns=normalized_field_names, ranking_type=task_obj.ranking_type,
                           shortlist_button=configs["ui_display_config"]["shortlist_button"])


@app.route('/get_factual_xai_detail/<doc_id>/<ranking_type>', methods=['GET'])
def get_factual_xai_detail(doc_id, ranking_type):
    doc_obj = database.DocRepr.objects(_id=doc_id).first()
    if not doc_obj:
        return "Document not found", 404

    _, doc_obj = get_xai_data(doc_obj, ranking_type, type="factual")

    return render_template(
        'doc_ranking_view_plot_and_description_factual_XAI_template.html', session_id=session['user_id'],
        doc_obj=doc_obj
    )




@app.route("/form/", methods=['GET', 'POST'])
# @login_required
def exit_form():
    """
    Renders the 'form_template.html' template
    with the items specified in the 'exit_survey' configuration.

    Returns:
        The rendered template.
    """
    survey_title = ' '.join(
        word.capitalize() for word in configs['ui_display_config']['exit_survey']['title'].split('_'))
    survey_description = ''
    if 'description' in configs['ui_display_config']['exit_survey']:
        survey_description = configs['ui_display_config']['exit_survey']['description']
    return render_template('form_template.html', session_id=session['user_id'],
                           items=configs['ui_display_config']['exit_survey']['questions'],
                           survey_title=survey_title, survey_description=survey_description)


@app.route("/questionnaire/<int:experiment_id>/<n_task>", methods=['GET', 'POST'])
# @login_required
def questionnaire(experiment_id, n_task):
    """
    Renders the form template with questionnaire questions.
    Handles user progress and redirects to the next appropriate URL based on the
    experiment's JSON task sequence, without relying on hardcoded questionnaire titles.

    Returns:
        The rendered template with the questionnaire questions.
    """
    # Mark the current questionnaire task as visited by the user
    user = database.User.objects(_user_id=session['user_id']).first()
    if n_task not in [item.task for item in user.tasks_visited]:
        task_visited = database.TaskVisited(task=str(n_task), exp=str(experiment_id))
        user.tasks_visited.append(
            task_visited)  # This uses read-modify-write, consider atomic update for high concurrency on same user.
        user.save()

    # Get the next task index using the updated get_next_task logic
    response = get_next_task(experiment_id)
    next_task_data = response.get_json()
    next_task_idx = next_task_data['next_task']  # This is the index of the next task in the JSON array

    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()

    # Get the current task object to retrieve its questionnaire questions
    current_task_id = exp_obj.tasks[int(n_task)]
    current_task_obj = database.Task.objects(id=current_task_id).first()

    question_list = current_task_obj.questionnaire  # Retrieve questions from the current task object

    # Determine the next URL based on the next_task_idx provided by get_next_task
    if next_task_idx == 'form':  # If next_task_idx signals a general final form (from config)
        next_url = url_for('exit_form')
    elif next_task_idx == 'stop_experiment':  # If next_task_idx signals experiment completion
        next_url = url_for('stop_experiment')
    else:
        # We have a valid task index, retrieve the next task object from the database
        next_task_id = exp_obj.tasks[int(next_task_idx)]
        next_task_obj = database.Task.objects(id=next_task_id).first()

        # Decide redirection based on the TYPE of the NEXT task
        if next_task_obj.ranking_type == "form":  # If the NEXT task is another questionnaire
            next_url = url_for('questionnaire', experiment_id=experiment_id, n_task=next_task_idx)
        else:  # Otherwise, the NEXT task is a ranking task
            next_url = url_for('index_ranking', experiment_id=experiment_id, n_task=next_task_idx, doc_id="view")

    original_title = current_task_obj.query_title.lower()
    survey_title = ' '.join(word.capitalize() for word in original_title.split('_'))
    task_description = get_task_description(current_task_obj)

    survey_description = ''
    if hasattr(current_task_obj, 'description') and current_task_obj.description:
        survey_description = current_task_obj.description

    return render_template('form_template_task_questionnaire.html', session_id=session['user_id'], items=question_list,
                           next_url=next_url, current_task=n_task, experiment_id = experiment_id,
                           survey_title=survey_title, survey_description=survey_description,
                           task_description=task_description)


def check_attention(experiment_id, current_task, form_results):
    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
    task_id = exp_obj.tasks[int(current_task)]
    task_obj = database.Task.objects(id=task_id).first()

    if "attention_check" in configs:
        fail_question = False
        user = database.User.objects(_user_id=session['user_id']).first()
        attention_questions = [q for q in task_obj.questionnaire if "correct_answer" in q]
        if len(attention_questions) > 0:

            current_fail_count = user._attention_check if user._attention_check else "0"
            current_reload_count = user._reload_attention_check if user._reload_attention_check else "0"

            for attention_question in attention_questions:
                question_field = attention_question["field"]
                user_answer = form_results.get(question_field)

                if user_answer != attention_question["correct_answer"]:
                    fail_question = True
                    break  # One failure is enough to count as a failed task

        if fail_question:
            if str(current_task) in configs["attention_check"]["reload_tasks"]:
                user._reload_attention_check = str(int(current_reload_count) + 1)
            else:
                user._attention_check = str(int(current_fail_count) + 1)
            user.save()

        return {
                    "attention_limit": int(user._attention_check or 0) < configs["attention_check"]["limit"],
                    "attention_passed": not fail_question,
                    "attention_reload": str(current_task) in configs["attention_check"]["reload_tasks"]
                }
    return {
                "attention_limit": True,
                "attention_passed": False,
                "attention_reload": True
            }

@app.route('/store_data_ranking', methods=['POST'])
def store_data_ranking():
    """
    Stores the annotation data received from the user to the MongoDB database.

    Returns:
        str: A string indicating the success of the operation.
    """
    data = request.get_json()
    logger.info(f"Data received: {data}")
    n_task = data.get('nTask')
    interactions = data.get('interactions')
    orderCheckbox = data.get('orderCheckBox', [])

    all_interactions = []
    for doc_id, info in interactions.items():
        interactions_document = database.Interaction(
            doc_id=doc_id,
            # Factual Explanation interactions
            view_factual=str(info.get('view_factual', 0)),
            view_factual_timestamps=info.get('view_factual_timestamps', []),

            # Counterfactual Explanation interactions
            view_counterfactual=str(info.get('view_counterfactual', 0)),
            view_counterfactual_timestamps=info.get('view_counterfactual_timestamps', []),

            # Image Explanation interactions
            view_image=str(info.get('view_image', 0)),
            view_image_timestamps=info.get('view_image_timestamps', []),

            # Text Explanation interactions
            view_text=str(info.get('view_text', 0)),
            view_text_timestamps=info.get('view_text_timestamps', []),

            # Combined Image-Text Explanation interactions
            view_image_text=str(info.get('view_image_text', 0)),
            view_image_text_timestamps=info.get('view_image_text_timestamps', []),

            # Shortlist status
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
    return "ok"


@app.route("/task_questionnaire_submit", methods=['POST']) # Removed URL param for easier JS calls
def task_questionnaire_submit():
    data = request.get_json()
    form_results = data.get('form_results', {})
    current_task = data.get('nTask')
    experiment_id = data.get('expID')

    user = database.User.objects(_user_id=session['user_id']).first()

    if user:
        target_task = next((t for t in user.tasks_visited if str(t.task) == str(current_task)), None)

        if target_task:
            target_task.form_submission = form_results
            user.save()
        else:
            print(f"Error: Task {current_task} not found in user's visited tasks.")
        result = check_attention(experiment_id, current_task, form_results)

        return jsonify({
            "attention_limit": result["attention_limit"],
            "attention_reload": result["attention_reload"],
            "attention_passed": result["attention_passed"]
        })



@app.route("/form_submit", methods=['GET', 'POST'])
# @login_required
def form_submit():
    """
    Stores the data collected in the form to the MongoDB database.

    Returns:
        str: A string indicating the success of the operation.
    """
    data = request.get_json()
    logger.info(f"Data received mongodb: {data}")
    form_results = data.get('form_results', [])

    user = database.User.objects(_user_id=session['user_id']).first()
    user.exit_form = form_results
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

        try:
            user = database.User.objects(_user_id=session['user_id']).first()

            # Ensure the field exists and is numeric
            attention_value = int(user._attention_check or 0)

            if attention_value >= configs["attention_check"]["limit"]:
                prolific_code = "FAIL"
            else:
                prolific_code = "PASS"
            return render_template('stop_experiment_template.html', prolific_code=prolific_code)
        except Exception as e:
            # Log the error for debugging (optional)
            print(f"Redirect failed or user missing field: {e}")
            # Fallback render
            return render_template('stop_experiment_template.html', prolific_code="")
    else:
        return render_template('stop_experiment_template.html', prolific_code="")


@app.route("/404/<error>", methods=['GET', 'POST'])
# @login_required
def error_handling(error):
    return render_template('404.html', error=error)



if __name__ == "__main__":
        if os.path.exists(args.config_path):
            app.run(debug=True, use_reloader=False, host='0.0.0.0',
                    port=args.port)  # with this we dont need to stop the running flask app, only need to refresh the page in the browser to load the new changes

