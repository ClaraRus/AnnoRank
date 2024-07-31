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
import importlib

import pandas as pd
from mongoengine import *
import json
from src.utils import add_fields_from_data
from src.constants import fairness_method_mapping
from src.constants import ranker_mapping

import database
from src.utils import read_json
import os

parser = argparse.ArgumentParser()
parser.add_argument('--config_path')
args = parser.parse_args()
config = read_json(args.config_path)

connect(config["data_reader_class"]["name"], host='mongo', port=27017)
#connect(config["data_reader_class"]["name"], host=f'mongodb://{"mongo-container"}:{27017}/{config["data_reader_class"]["name"]}', port=27017)
#connect(config["data_reader_class"]["name"], host='0.0.0.0', port=27017)

def add_fields_from_data(attr_names, values, object):
    """Add data of user responses for various assigned tasks. 

    This function takes a list of new features (attr_names) and their corresponding values (values),
    and adds them to a given database object (object). Each feature is associated with a single user,
    representing their response to a specific task.

    Args:
        attr_names (List): A list of new features that we want to associate with a single user.
        values (List): A list of values based on the attr_names.
        object (Database object): The database object that we want to add new data into.

    Returns:
        Database object: The updated database object with the new data added.
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


def add_exp_to_db(data_exp):
    """
    Adding experiment to the database based on what is defined in the config files, for instance experiment_annotate_score.json.

    Args:
        data_exp (list): A list of dictionaries containing information about the experiments.

    Returns:
        None
    """
    for exp_info in data_exp:
        exp_obj = database.Experiment.objects(_exp_id=str(exp_info['exp_id'])).first()

        tasks_obj = []
        for task in exp_info['tasks']:
            query_obj = database.QueryRepr.objects(title=task['query_title']).first()
            if query_obj is not None:
                data_obj = database.Data.objects(query=str(query_obj._id)).first()
                if data_obj is not None:
                    if 'index' in task.keys():
                        task_obj = database.TaskScore.objects(data=str(data_obj._id), ranking_type=task['ranking_type'], index=str(task['index'])).first()
                        if not task_obj:
                            task_obj = database.TaskScore()
                            task_obj = add_fields_from_data(list(task.keys()), list(task.values()), task_obj)
                            task_obj.ranking_type = task['ranking_type']
                    elif 'ranking_type' in task.keys():
                        task_obj = database.Task.objects(data=str(data_obj._id), ranking_type=task['ranking_type']).first()
                        if not task_obj:
                            task_obj = database.Task()
                            task_obj = add_fields_from_data(list(task.keys()), list(task.values()), task_obj)
                            task_obj.ranking_type = task['ranking_type']
                    elif 'ranking_type_2' in task.keys():
                        task_obj = database.TaskCompare.objects(data=str(data_obj._id), ranking_type_1=task['ranking_type_1'], ranking_type_2=task['ranking_type_2']).first()
                        if not task_obj:
                            task_obj = database.TaskCompare()
                            task_obj = add_fields_from_data(list(task.keys()), list(task.values()), task_obj)
                            task_obj.ranking_type_1 = task['ranking_type_1']
                            task_obj.ranking_type_2 = task['ranking_type_2']

                    task_obj.data = str(data_obj._id)
                    task_obj.save()

                    if not exp_obj or (not str(task_obj.auto_id_0) in exp_obj.tasks or not str(task_obj._id) in exp_obj.tasks):
                        tasks_obj.append(str(task_obj.auto_id_0))

        if exp_obj:
            if len(tasks_obj) > 0:
                exp_obj.tasks.extend(tasks_obj)
        else:
            if not exp_obj and tasks_obj is not None:
                exp_obj = database.Experiment(_exp_id=str(exp_info['exp_id']), _description=exp_info['description'], tasks=tasks_obj)
        exp_obj.save()


def add_query_docs_to_db(data, query_col, data_configs):
    """Adding query to the database based on what is defined in the config files, for instance config_annotate_score_xing.json for xing tutorial. 

    Args:
        data (Dataframe): query dataframe
        query_col (String): column in the dataset that is assigned as a query text
        data_configs (List): List of config features
    """
    fields = list(data_configs.values())
    for query, group in data['docs'].groupby(query_col):
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


def add_data_to_db(data, fields, ranking_type, query_col, sort_col='score', ascending=False):
    """Adding document data to the database based on what is defined in the config files, for instance config_annotate_score_xing.json for xing tutorial. 

    Args:
        data (Dataframe): document dataframe
        fields (String): column in the dataset that is assigned as a query text
        data_configs (List): List of config features
    """
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
                        else:
                            columns = ["prediction"]
                            max_ = max(group[data['docs'].columns[-1]]) + 1
                            values = [max_ - row[data['docs'].columns[-1]]]
                            add_fields_from_data(columns, values, pre_doc)
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
        else:
            continue


def get_docs_df(ranking_type, data_config, features):
    """Retrieve document dataframe 
    get_docs_df(train_data, self.config['data_reader_class'], setting['features'])
    Args:
        ranking_type (_type_): The ranking type can be original, preprocessing based on what is defined in the train_ranker_config
        data_config (_type_): Config of the dataset from
        features (_type_): _description_

    Returns:
        _type_: _description_
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


class Pipeline:
    def __init__(self, config):
        self.config = config
        self.data_reader = getattr(
            importlib.import_module("src.data_readers.data_reader_" + self.config['data_reader_class']["name"]),
            "DataReader" + self.config['data_reader_class']["name"].title())(configs=self.config['data_reader_class'])

    def read_data(self):
        """Read data from json file to dataframe

        Returns:
            dataset splitted into training and test data. 
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
        Trains the ranking model based on the specified ranking library.

        This method iterates over the settings specified in the `train_ranker_config` section of the config file.
        For each setting, it creates an instance of the specified ranking library and trains the model using the
        provided training and test data. It then predicts the ranking for the test data and stores the results in
        the database.

        Note: The `train_ranker_config` section in the config file should contain the following keys:
        - `name`: The name of the ranking library to use.
        - `settings`: A list of dictionaries, where each dictionary represents a specific setting for training the model.
          Each dictionary should contain the following keys:
          - `train_data`: A list of paths to the training data files.
          - `test_data`: A list of paths to the test data files.
          - `features`: A list of features to use for training the model.
          - `ranking_type`: The type of ranking to perform.

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
        """Apply fairness into the dataset features based on the data_reader_class attributes. 

         Args:
            fields (Object data)
                attributes of the data_reader_class except name
            config_method_key (Object data)
                apply either pre-processing or post-processing fairness intervention
            sort_column (String)
                sort data based on certain columns, for instance, average_review_rating
            ascending (boolean)
                True or False, if set to True, then the displayed ranking with fairness intervention will be shown in ascending manner.
        """
        already_added_rankings = [r_type for r_type in [item.ranking_type for item in database.Data.objects().first().rankings]]
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
                            ranking_type = ranking_type + train_data + ":" + self.config['data_reader_class']['score'] + '_fair__'
                        else:
                            ranking_type = ranking_type + self.config['data_reader_class']['score'] + '__'
                    else:
                        if not 'original' in test_data:
                            if 'ranker' not in test_data:
                                ranking_type = ranking_type + test_data + ":" + self.config['data_reader_class']['score'] + '_fair__'
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
        add_query_docs_to_db(data_test, self.config['data_reader_class']['query'],
                             self.config['data_reader_class'])
        fields = [f for f in list(self.config['data_reader_class'].values()) if f != self.config['data_reader_class']['name']]
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
