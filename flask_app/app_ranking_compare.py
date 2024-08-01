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
import os
import logging

import database
from flask import Flask, render_template, redirect, make_response, jsonify
from flask_login import LoginManager
from mongoengine import *

from config import Config
from evaluate.evaluate import get_fairness_metrics, get_utility_metrics, get_average_interactions

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

connect(configs["data_reader_class"]["name"],
        host=f'mongodb://{"mongo-container"}:{27017}/{configs["data_reader_class"]["name"]}', port=27017)
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
@app.route("/start_compare/<int:experiment_id>", methods=['GET', 'POST'])
def start_compare(experiment_id):
    """
    Redirects to the next task URL for the given experiment ID.

    Args::
        experiment_id (int): The ID of the experiment.

    Returns:
        response (flask.Response): The redirect response with the next task URL.
    """
    url = str(experiment_id) + '/index_compare/' + str(0)
    response = make_response(redirect(url, code=200))
    response.headers['HX-Redirect'] = url
    return response


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
    """Renders Ranking Comparison UI for researchers.

    Args:
        experiment_id (str): The ID of the experiment.
        n_task (int): The index of the task.

    Returns:
        render_template: The rendered HTML template for the index_ranking_compare_template.

    """
    try:
        exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()
        task_id = exp_obj.tasks[int(n_task)]

        task_obj = database.TaskCompare.objects(_id=task_id).first()
        data_obj = database.Data.objects(_id=task_obj.data).first()
        query_obj = database.QueryRepr.objects(_id=data_obj.query).first()
    except:
        response = make_response(redirect(f"/404/Experiment type is not for app_compare!", code=200))
        response.headers['HX-Redirect'] = f"/404/Experiment type is not for app_compare!"
        return response

    try:
        docs = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type_1][0].docs
    except:
        response = make_response(redirect(f"/404/No document with the ranking type!", code=200))
        response.headers['HX-Redirect'] = f"/404/No document with the ranking type!"
        return response

    docs_obj_1 = [database.DocRepr.objects(_id=doc_id).first() for doc_id in docs]

    try:
        docs = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type_2][0].docs
    except:
        response = make_response(redirect(f"/404/No document with the ranking type!", code=200))
        response.headers['HX-Redirect'] = f"/404/No document with the ranking type!"
        return response

    docs_obj_2 = [database.DocRepr.objects(_id=doc_id).first() for doc_id in docs]

    doc_field_names_display = configs["ui_display_config"]["display_fields"]

    query_title = query_obj.title
    query_text = query_obj.text

    current_url = '/start_compare/' + str(experiment_id) + '/index_compare/' + str(n_task) + '/'
    view_configs = configs["ui_display_config"]

    interactions = get_average_interactions(configs["ui_display_config"]["avg_interaction"]["experiment_id"],
                                            interaction=configs["ui_display_config"]["avg_interaction"]["interaction"])

    fairness_metrics = dict()
    utility_metrics = dict()
    if "display_metrics" in configs["ui_display_config"]:
        utility_metrics[task_obj.ranking_type_1] = get_utility_metrics(configs, docs_obj_1)
        utility_metrics[task_obj.ranking_type_2] = get_utility_metrics(configs, docs_obj_2)
        fairness_metrics[task_obj.ranking_type_1] = get_fairness_metrics(configs, docs_obj_1)
        fairness_metrics[task_obj.ranking_type_2] = get_fairness_metrics(configs, docs_obj_2)
    else:
        utility_metrics[task_obj.ranking_type_1] = []
        utility_metrics[task_obj.ranking_type_2] = []
        fairness_metrics[task_obj.ranking_type_1] = []
        fairness_metrics[task_obj.ranking_type_2] = []

    return render_template('index_ranking_compare_template.html', doc_field_names=doc_field_names_display,
                           avg_interaction=interactions, utility_metrics=utility_metrics,
                           fairness_metrics=fairness_metrics,
                           view_configs=view_configs,
                           doc_data_objects_1=docs_obj_1, doc_data_objects_2=docs_obj_2,
                           ranking_type_1=task_obj.ranking_type_1, ranking_type_2=task_obj.ranking_type_2,
                           query_title=query_title, query_text=query_text, current_url=current_url,
                           task_description=configs["ui_display_config"]["task_description"])


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True, host='0.0.0.0',
            port=5001)  # with this we dont need to stop the running flask app, only need to refresh the page in the browser to load the new changes
