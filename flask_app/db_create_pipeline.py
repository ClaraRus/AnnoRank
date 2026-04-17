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
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

import argparse
import importlib
import database
import os
import pandas as pd
from mongoengine import *

from utils.utils import add_fields_from_data
from utils.constants import fairness_method_mapping
from utils.constants import ranker_mapping
from utils.utils import read_json

parser = argparse.ArgumentParser()
parser.add_argument('--config_path')
args = parser.parse_args()
config = read_json(args.config_path)

connect(config["data_reader_class"]["name"], host='mongo', port=27017)

import logging

logging.basicConfig(filename='../record.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def add_fields_from_data(attr_names, values, object):
    """Add dynamic fields to an object from the database.

    Args:
        attr_names (List): A list of new fields that we want to add to the object.
        values (List): A list of values to be inserted in the database for the corresponding field.
        object (Database object): The database object to which we want to add dynamic fields.

    Returns:
        Database object: The updated database object with the new fields and values.
    """
    for index, attr_name in enumerate(attr_names):
        object.__setattr__(attr_name, values[index])

    return object


def get_doc_object_in_db(attr_names, values, display_fields):
    """
    Retrieves a document object from the database based on the provided attribute names, values, and display fields.

    Args:
        attr_names (list): A list of attribute names.
        values (list): A list of corresponding attribute values.
        display_fields (list): A list of fields to be displayed.

    Returns:
        doc_obj: The document object retrieved from the database.
    """
    filter_ = {attr: value for attr, value in zip(attr_names, values) if attr in display_fields}
    doc_obj = database.DocRepr.objects.filter(**filter_).first()
    return doc_obj


# In file: flask_app/db_create_pipeline.py

def add_exp_to_db(data_exp):
    """
    Adds experiment data to the database based on the provided experiment configurations.
    Ensures that 'form' tasks (questionnaires) are uniquely identified per experiment.

    Args:
        data_exp (list): A list of dictionaries, where each dictionary contains
                         information about an experiment, including its tasks.
    Returns:
        None
    """

    for exp_info in data_exp:
        exp_id_str = str(exp_info['exp_id']) # Get experiment ID as string for unique naming

        # Try to find the experiment in the database
        exp_obj = database.Experiment.objects(_exp_id=exp_id_str).first()

        tasks_obj_ids_for_exp = [] # This list will hold the IDs of tasks in the correct order for this experiment

        for task_data_from_json in exp_info["tasks"]:
            current_task_obj = None
            query_obj = database.QueryRepr.objects(title=task_data_from_json.get("query_title")).first()
            data_obj = None
            if query_obj:
                data_obj = database.Data.objects(query=str(query_obj._id)).first()

            # --- 1️⃣ Handle FORM tasks first ---
            if task_data_from_json.get("ranking_type") == "form":
                original_query_title = task_data_from_json.get("query_title", "unknown_form_title")
                unique_form_query_title = f"exp{exp_id_str}_{original_query_title}"

                filter_kwargs = {
                    "query_title": unique_form_query_title,
                    "ranking_type": "form",
                    "questionnaire": task_data_from_json.get("questionnaire"),
                    "show_xai": task_data_from_json.get("show_xai"),
                }
                if "cand_idx" in task_data_from_json:
                    filter_kwargs["cand_idx"] = task_data_from_json["cand_idx"]

                current_task_obj = database.Task.objects(**filter_kwargs).first()

                if not current_task_obj:
                    current_task_obj = database.Task()
                    task_data_to_save = task_data_from_json.copy()
                    task_data_to_save["query_title"] = unique_form_query_title
                    current_task_obj = add_fields_from_data(
                        list(task_data_to_save.keys()), list(task_data_to_save.values()), current_task_obj
                    )
                    current_task_obj.ranking_type = "form"
                    current_task_obj.data = "form"  # or adjust type if data is a ReferenceField
                    current_task_obj.save()
                    logger.debug(
                        f"CREATED Form Task: {unique_form_query_title} (Original: {original_query_title}) "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )
                else:
                    task_data_to_save = task_data_from_json.copy()
                    task_data_to_save["query_title"] = unique_form_query_title
                    current_task_obj = add_fields_from_data(
                        list(task_data_to_save.keys()), list(task_data_to_save.values()), current_task_obj
                    )
                    current_task_obj.ranking_type = "form"
                    current_task_obj.data = "form"
                    current_task_obj.save()
                    logger.debug(
                        f"FOUND/UPDATED Form Task: {unique_form_query_title} (Original: {original_query_title}) "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )

            # --- 2️⃣ Tasks that reference show_xai ---
            elif "show_xai" in task_data_from_json:

                filter_kwargs = {
                    "data": str(data_obj._id) if data_obj else None,
                    "ranking_type": task_data_from_json.get("ranking_type"),
                    "questionnaire": task_data_from_json.get("questionnaire"),
                    "show_xai": task_data_from_json.get("show_xai"),
                }
                if "cand_idx" in task_data_from_json:
                    filter_kwargs["cand_idx"] = task_data_from_json["cand_idx"]

                current_task_obj = database.Task.objects(**filter_kwargs).first()
                if not current_task_obj:
                    current_task_obj = database.Task()
                    current_task_obj = add_fields_from_data(
                        list(task_data_from_json.keys()), list(task_data_from_json.values()), current_task_obj
                    )
                    current_task_obj.ranking_type = task_data_from_json["ranking_type"]
                    current_task_obj.data = str(data_obj._id) if data_obj else None
                    current_task_obj.save()
                    logger.debug(
                        f"CREATED Task (show_xai): {task_data_from_json.get('query_title', 'N/A')} "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )
                else:
                    current_task_obj = add_fields_from_data(
                        list(task_data_from_json.keys()), list(task_data_from_json.values()), current_task_obj
                    )
                    current_task_obj.ranking_type = task_data_from_json["ranking_type"]
                    current_task_obj.data = str(data_obj._id) if data_obj else None
                    current_task_obj.save()
                    logger.debug(
                        f"FOUND/UPDATED Task (show_xai): {task_data_from_json.get('query_title', 'N/A')} "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )

            # --- 3️⃣ TaskScore branch (index) ---
            elif "index" in task_data_from_json:
                current_task_obj = database.TaskScore.objects(
                    data=str(data_obj._id) if data_obj else None,
                    ranking_type=task_data_from_json["ranking_type"],
                    index=str(task_data_from_json["index"]),
                ).first()
                if not current_task_obj:
                    current_task_obj = database.TaskScore()
                    current_task_obj = add_fields_from_data(
                        list(task_data_from_json.keys()), list(task_data_from_json.values()), current_task_obj
                    )
                    current_task_obj.ranking_type = task_data_from_json["ranking_type"]
                    current_task_obj.data = str(data_obj._id) if data_obj else None
                    current_task_obj.save()
                    logger.debug(
                        f"CREATED TaskScore: {task_data_from_json.get('query_title', 'N/A')} "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )
                else:
                    current_task_obj = add_fields_from_data(
                        list(task_data_from_json.keys()), list(task_data_from_json.values()), current_task_obj
                    )
                    current_task_obj.ranking_type = task_data_from_json["ranking_type"]
                    current_task_obj.data = str(data_obj._id) if data_obj else None
                    current_task_obj.save()
                    logger.debug(
                        f"FOUND/UPDATED TaskScore: {task_data_from_json.get('query_title', 'N/A')} "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )

            # --- 4️⃣ TaskCompare branch ---
            elif "ranking_type_2" in task_data_from_json:
                current_task_obj = database.TaskCompare.objects(
                    data=str(data_obj._id) if data_obj else None,
                    ranking_type_1=task_data_from_json["ranking_type_1"],
                    ranking_type_2=task_data_from_json["ranking_type_2"],
                ).first()
                if not current_task_obj:
                    current_task_obj = database.TaskCompare()
                    current_task_obj = add_fields_from_data(
                        list(task_data_from_json.keys()), list(task_data_from_json.values()), current_task_obj
                    )
                    current_task_obj.ranking_type_1 = task_data_from_json["ranking_type_1"]
                    current_task_obj.ranking_type_2 = task_data_from_json["ranking_type_2"]
                    current_task_obj.data = str(data_obj._id) if data_obj else None
                    current_task_obj.save()
                    logger.debug(
                        f"CREATED TaskCompare: {task_data_from_json.get('query_title', 'N/A')} "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )
                else:
                    current_task_obj = add_fields_from_data(
                        list(task_data_from_json.keys()), list(task_data_from_json.values()), current_task_obj
                    )
                    current_task_obj.ranking_type_1 = task_data_from_json["ranking_type_1"]
                    current_task_obj.ranking_type_2 = task_data_from_json["ranking_type_2"]
                    current_task_obj.data = str(data_obj._id) if data_obj else None
                    current_task_obj.save()
                    logger.debug(
                        f"FOUND/UPDATED TaskCompare: {task_data_from_json.get('query_title', 'N/A')} "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )

            # --- 5️⃣ Generic ranking tasks (fallback) ---
            elif "ranking_type" in task_data_from_json:
                current_task_obj = database.Task.objects(
                    data=str(data_obj._id) if data_obj else None,
                    ranking_type=task_data_from_json["ranking_type"],
                ).first()
                if not current_task_obj:
                    current_task_obj = database.Task()
                    current_task_obj = add_fields_from_data(
                        list(task_data_from_json.keys()), list(task_data_from_json.values()), current_task_obj
                    )
                    current_task_obj.ranking_type = task_data_from_json["ranking_type"]
                    current_task_obj.data = str(data_obj._id) if data_obj else None
                    current_task_obj.save()
                    logger.debug(
                        f"CREATED Generic Ranking Task: {task_data_from_json.get('query_title', 'N/A')} "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )
                else:
                    current_task_obj = add_fields_from_data(
                        list(task_data_from_json.keys()), list(task_data_from_json.values()), current_task_obj
                    )
                    current_task_obj.ranking_type = task_data_from_json["ranking_type"]
                    current_task_obj.data = str(data_obj._id) if data_obj else None
                    current_task_obj.save()
                    logger.debug(
                        f"FOUND/UPDATED Generic Ranking Task: {task_data_from_json.get('query_title', 'N/A')} "
                        f"for Exp {exp_id_str} with ID {current_task_obj.id}"
                    )

            # --- 6️⃣ Unexpected / fallback ---
            else:
                logger.warning(f"Task with unexpected structure: {task_data_from_json}")
                continue

            # Append task id to experiment
            if current_task_obj:
                tasks_obj_ids_for_exp.append(str(current_task_obj.id))
            else:
                logger.error(f"Failed to process task: {task_data_from_json}")

        # --- Final Experiment Save Logic ---
        # After processing all tasks for the current experiment:
        if exp_obj: # If the experiment already exists in the database
            # Replace the entire tasks list with the newly collected and ordered IDs
            exp_obj.tasks = tasks_obj_ids_for_exp
            # AGGIUNGI O AGGIORNA ALTRI CAMPI DELL'ESPERIMENTO SE NECESSARIO QUI
            exp_obj._description = exp_info.get('description', f"Experiment {exp_id_str}") # Aggiorna la descrizione anche per gli esperimenti esistenti
            logger.info(f"Existing experiment {exp_id_str} updated with new task order.")
        else: # If the experiment does not exist, create it
            logger.info(f"Creating new experiment {exp_id_str} with defined tasks.")
            exp_obj = database.Experiment(
                _exp_id=exp_id_str,
                # CORREZIONE: Cambia 'description' in '_description' per allinearlo al modello del database
                _description=exp_info.get('description', f"Experiment {exp_id_str}"),
                tasks=tasks_obj_ids_for_exp
            )
        exp_obj.save() # Save the updated or newly created Experiment object
        logger.info(f"Experiment {exp_id_str} saved successfully with tasks: {exp_obj.tasks}")

def add_query_docs_to_db(data, data_configs):
    """Adding query and documents to the database.
    Args:
        data (dict): dict containing the query dataframe and the document dataframe.
        data_configs (dict): configuration dict of the dataset.
    """
    fields = list(data_configs.values())
    for query, group in data['docs'].groupby(data_configs['query']):
        query_obj = database.QueryRepr.objects(title=query).first()

        if not query_obj:
            query_text = data['query'][data['query']['title'] == query]['text'].values[0]
            query_obj = database.QueryRepr(title=query, text=query_text)
            query_obj.save()

        for _, row in group.iterrows():
            doc_obj = get_doc_object_in_db(data['docs'].columns, row.values, fields)
            if not doc_obj:
                doc_obj = database.DocRepr()
                doc_obj = add_fields_from_data(data['docs'].columns, row.values, doc_obj)
                doc_obj.save()


def add_data_to_db(data, fields, ranking_type, query_col, sort_col='score', ascending=True):
    """Adding query-ranking pairs in the database (Data object).
        If pre-processing fairness methods are applied the changed data will be added in the database (DocRepr object).

    Args:
        data (dict): dict containing the query dataframe and the document dataframe.
        fields (list(str)): list of fields defined for the document.
        ranking_type (str): ranking type of the ranking to be added in the database
            (e.g. original if ranking is done based on the original value of sort_col,
            else depends on the ranker model or fairness intervention applied on the data).
        query_col (str): column name defined as the query.
        sort_col (str): column name to sort the documents in the ranking.
        ascending (bool): True if sorting by sort_col in ascending order, else in descending order.
    """
    data['docs'] = data['docs'][data['docs'][sort_col] != ""]

    data['docs'] = data['docs'].groupby(query_col).apply(
        lambda x: x.sort_values(sort_col, ascending=ascending)).reset_index(drop=True)

    for query, group in data['docs'].groupby(query_col):
        doc_list = []

        query_obj = database.QueryRepr.objects(title=query).first()
        if query_obj:
            for _, row in group.iterrows():
                doc_obj = get_doc_object_in_db(data['docs'].columns, row.values, fields)
                if 'original' not in ranking_type:
                    if ranking_type not in doc_obj:
                        add_fields_from_data([ranking_type], [[]], doc_obj)
                        already_added = False
                    else:
                        already_added = len(
                            [predoc for predoc in doc_obj[ranking_type] if predoc.ranking_type == ranking_type]) > 0

                    if not already_added:
                        pre_doc = database.PreDocRepr(ranking_type=ranking_type)
                        if ranking_type.startswith('preprocessing'):
                            columns_fair = [col for col in data['docs'].columns if '_fair' in col]
                            values_fair = [row[col] for col in columns_fair]
                            add_fields_from_data(columns_fair, values_fair, pre_doc)
                        # else:
                        #     columns = ["prediction"]
                        #     max_ = max(group[data['docs'].columns[-1]]) + 1
                        #     values = [max_ - row[data['docs'].columns[-1]]]
                        #     add_fields_from_data(columns, values, pre_doc)
                        doc_obj[ranking_type].append(pre_doc)
                        doc_obj.save()

                doc_list.append(doc_obj._id)

            ranking_obj = database.Ranking(ranking_type=ranking_type, docs=doc_list)
            data_obj = database.Data.objects(query=str(query_obj._id)).first()
            if not data_obj:
                data_obj = database.Data(query=str(query_obj._id), rankings=[ranking_obj])
                data_obj.save()
            else:
                saved_rankings = [r.ranking_type for r in data_obj.rankings]
                if ranking_obj.ranking_type not in saved_rankings:
                    data_obj.rankings.append(ranking_obj)
                    data_obj.save()




def get_docs_df(ranking_type, data_config, features):
    """Retrieve documents representation from the database and converts in dataframe.
    Args:
        ranking_type (str): If set to preprocessing, it retrieves the document representation
            transformed by the preprocessing fairness method.
            If set to original it retrieves the original document representation.
        data_config (dict): Configuration dict of the dataset.
        features (list(str)): List of columns representing the features of the document.

    Returns:
        df (pandas.DataFrame): dataframe containing the retrieved document representation from the database.
    """

    data_list = []
    for doc in database.DocRepr.objects():
        if 'original' not in ranking_type:
            field_list = [data_config['query'], data_config['docID'], data_config['group']]

            if ranking_type.startswith('preprocessing'):
                sub_columns = [col + '_fair' for col in features]
                sub_columns.append(data_config['score'] + '_fair')
            else:
                sub_columns = ["prediction"]
            field_list.extend(sub_columns)

            data_list.append({field: getattr(doc, field, None) if field not in sub_columns else getattr(
                doc[ranking_type][0], field, None) for field in field_list})
        else:
            field_list = [data_config['query'], data_config['docID'], data_config['group']]
            field_list.extend(features)
            field_list.append(data_config['score'])
            data_list.append({field: getattr(doc, field, None) for field in field_list})


    # Create a Pandas DataFrame from the list of dictionaries
    df = pd.DataFrame(data_list)
    return df

def add_data_to_db_from_ranking_file(data_name, data_test, fields, query_col, doc_ID_col):
    data_docs = data_test['docs']
    queries = data_docs[query_col].unique()
    for query in queries:
        path_ranking_files = os.path.join("./dataset", data_name, "data", query)
        ranking_files = [file for file in os.listdir(path_ranking_files) if ".txt" in file]
        for ranking_file in ranking_files:
            path_ranking = os.path.join(path_ranking_files, ranking_file)
            with open(path_ranking, "r") as f:
                ranking_ids = list(map(int, f.readline().strip().split(',')))
                for rank, ranking_id in enumerate(ranking_ids):
                    # find row in data_test and add colum for ranking
                    path_file = os.path.join(path_ranking_files, f"{ranking_id}.json")
                    sort_col = ranking_file.strip(".txt")
                    if sort_col not in data_docs.columns:
                        data_docs[sort_col] = [""] * len(data_docs)
                    with open(path_file, 'r') as f:
                        data = json.load(f)
                    if not doc_ID_col in data:
                        column_docID = doc_ID_col.strip("_display")
                    else:
                        column_docID = doc_ID_col
                    if not column_docID in data:
                        column_docID = "_" + column_docID
                    else:
                        column_docID = doc_ID_col
                    data_docs.loc[data_docs[column_docID] == data[column_docID], sort_col] = rank + 1
            data_test['docs'] = data_docs
            add_data_to_db(data_test, fields=fields,
                   query_col=query_col,
                   sort_col=sort_col, ranking_type=sort_col)


class Pipeline:
    """
        Pipeline class for inserting the data in the database.
    """
    def __init__(self, config):
        """
        Pipeline init class.
        Attributes
        ----------
        config : dict
            configuration dict defined in the configuration file
        data_reader : DataReader
            DataReader object corresponding to the dataset defined in the configuration file
        query_col : str
        """
        self.config = config
        self.data_reader = getattr(
            importlib.import_module("data_readers.data_reader_" + self.config['data_reader_class']["name"]),
            "DataReader" + self.config['data_reader_class']["name"].title())(configs=self.config['data_reader_class'])

    def read_data(self):
        """Read data using the DataReader

        Returns:
            data_train (pandas.DataFrame): data used for training the ranker and/or the fairness intervention.
            data_test (pandas.DataFrame): data used for testing and displaying in the UI.
        """
        self.config['train_path'] = os.path.join(self.data_reader.output_file_path, 'train')
        self.config['test_path'] = os.path.join(self.data_reader.output_file_path, 'test')

        if os.path.exists(self.config['train_path']):
            data_train_docs, data_train_queries = self.data_reader.read('train')
            data_train = {
                "docs": data_train_docs,
                "query": data_train_queries
            }
        else:
            data_train = None

        if self.config['test_path']:
            data_test_docs, data_test_queries, experiments = self.data_reader.read('test')
            data_test = {
                "docs": data_test_docs,
                "query": data_test_queries,
                "exp": experiments
            }
        else:
            raise "You need to specify the Test Data as it is the dataset to be displayed!"

        return data_train, data_test

    def train_ranker(self):
        """
        Trains the ranking model based on the configurations defined under `train_ranker_config`.
        It saves the predicted ranking on the test split in the database.

        Returns:
        None
        """
        for setting in self.config['train_ranker_config']['settings']:
            ranker = ranker_mapping[self.config['train_ranker_config']['name']](
                setting, self.config['data_reader_class'],
                self.config['train_ranker_config']['model_path'])

            for train_data, test_data in zip(setting['train_data'], setting['test_data']):
                data_train = get_docs_df(train_data, self.config['data_reader_class'], setting['features'])
                data_test = get_docs_df(test_data, self.config['data_reader_class'], setting['features'])

                ranker.train_model(data_train, data_test, experiment=(train_data, test_data))
                data_test_dict = {
                    'docs': ranker.predict(data_test, experiment=(train_data, test_data))
                }

                ranking_type = setting['ranking_type'] + ":"
                if not 'original' in train_data:
                    sort_col = self.config['data_reader_class']['score'] + '_fair__'
                    ranking_type = ranking_type + train_data + ":" + sort_col
                else:
                    sort_col = self.config['data_reader_class']['score'] + '__'
                    ranking_type = ranking_type + sort_col
                if not 'original' in test_data:
                    sort_col = sort_col + self.config['data_reader_class']['score'] + '_fair'
                    ranking_type = ranking_type + self.config['data_reader_class']['score'] + '_fair'
                else:
                    sort_col = sort_col + self.config['data_reader_class']['score']
                    ranking_type = ranking_type + self.config['data_reader_class']['score']

                fields = [f for f in list(self.config['data_reader_class'].values()) if
                          f != self.config['data_reader_class']['name']]

                add_data_to_db(data_test_dict, fields=fields,
                               ranking_type=ranking_type,
                               query_col=self.config['data_reader_class']['query'], sort_col=sort_col, ascending=True)

    def apply_fair_method(self, fields, config_method_key, sort_column, ascending):
        """Apply fairness methods defined in the configuration file under `pre/in/post_processing_config`.
         Save the changed data (in case of pre-processing) and the new ranking in the database.
         Args:
            fields (list(str)): attributes of the document defined in the configuration file.
            config_method_key (str): can have the following values: pre_processing, in_processing and post_processing
                indicating which type of fairness method is applied.
            sort_column (str): column name after which the items are ranked.
            ascending (bool): True if sorting by sort_col in ascending order, else in descending order.
        """
        already_added_rankings = [r_type for r_type in
                                  [item.ranking_type for item in database.Data.objects().first().rankings]]
        for setting in self.config[config_method_key]['settings']:
            fairness_method = fairness_method_mapping[self.config[config_method_key]['name']](
                setting, self.config['data_reader_class'], self.config[config_method_key]['model_path'])
            if not setting['ranking_type'] in already_added_rankings:
                if "preprocessing" not in setting['ranking_type']:
                    if setting['train_data'] is None:
                        setting['train_data'] = [None] * len(setting['test_data'])

                    for train_data, test_data in zip(setting['train_data'], setting['test_data']):

                        if train_data is not None:
                            data_train = get_docs_df(train_data, self.config['data_reader_class'], setting['features'])
                            fairness_method.train_model(data_train)

                        if not 'features' in setting:
                            setting['features'] = []

                        data_test = get_docs_df(test_data, self.config['data_reader_class'], setting['features'])

                        data_test_dict = {
                            'docs': fairness_method.generate_fair_data(data_test)
                        }

                        ranking_type = setting['ranking_type'] + ":"

                        if train_data is not None:
                            if not 'original' in train_data:
                                ranking_type = ranking_type + train_data + ":" + self.config['data_reader_class'][
                                    'score'] + '_fair__'
                            else:
                                ranking_type = ranking_type + self.config['data_reader_class']['score'] + '__'
                        else:
                            if not 'original' in test_data:
                                if 'ranker' not in test_data:
                                    ranking_type = ranking_type + test_data + ":" + self.config['data_reader_class'][
                                        'score'] + '_fair__'
                                else:
                                    ranking_type = ranking_type.strip(":")
                            else:
                                ranking_type = ranking_type + self.config['data_reader_class']['score'] + '__'

                        if not 'original' in test_data:
                            if 'ranker' not in test_data:
                                ranking_type = ranking_type + test_data + ":" + self.config['data_reader_class'][
                                    'score'] + '_fair__'
                            else:
                                ranking_type = ranking_type.strip(":")
                        else:
                            ranking_type = ranking_type + self.config['data_reader_class']['score']

                        add_data_to_db(data_test_dict, fields=fields, ranking_type=ranking_type,
                                       query_col=self.config['data_reader_class']['query'],
                                       sort_col=sort_column, ascending=ascending)

                else:
                    data_train = get_docs_df("original", self.config['data_reader_class'], setting['features'])
                    data_test = get_docs_df("original", self.config['data_reader_class'], setting['features'])

                    fairness_method.train_model(data_train)
                    data_test_dict = {
                        'docs': fairness_method.generate_fair_data(data_test)
                    }
                    add_data_to_db(data_test_dict, fields=fields, ranking_type=setting['ranking_type'],
                                   query_col=self.config['data_reader_class']['query'],
                                   sort_col=sort_column, ascending=ascending)



    def run(self):
        database.create_collections()
        data_train, data_test = self.read_data()
        add_query_docs_to_db(data_test,
                             self.config['data_reader_class'])

        fields = [f for f in list(self.config['data_reader_class'].values()) if
                  f != self.config['data_reader_class']['name']]

        add_data_to_db_from_ranking_file(data_name=self.config['data_reader_class']['name'], data_test=data_test,
                                         fields=fields, query_col=self.config['data_reader_class']['query'], doc_ID_col=self.config['data_reader_class']['docID'])
        add_data_to_db(data_test, fields=fields,
                       query_col=self.config['data_reader_class']['query'],
                       sort_col=self.config['data_reader_class']['score'], ranking_type='original')

        add_exp_to_db(data_test['exp'])

        if self.config['pre_processing_config']:
            self.apply_fair_method(
                fields=fields,
                config_method_key='pre_processing_config',
                sort_column=self.config['data_reader_class']['score'] + '_fair', ascending=False)

        if self.config['train_ranker_config']:
            self.train_ranker()

        if self.config['post_processing_config']:
            self.apply_fair_method(
                fields=fields,
                config_method_key='post_processing_config',
                sort_column='rank_fair', ascending=True)


pipeline = Pipeline(config)
pipeline.run()


