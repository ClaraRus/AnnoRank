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


def add_exp_to_db(data_exp):
    """
    Adding experiment to the database based on what is defined in the experiment files
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
                        task_obj = database.TaskScore.objects(data=str(data_obj._id), ranking_type=task['ranking_type'],
                                                              index=str(task['index'])).first()
                        if not task_obj:
                            task_obj = database.TaskScore()
                            task_obj = add_fields_from_data(list(task.keys()), list(task.values()), task_obj)
                            task_obj.ranking_type = task['ranking_type']
                    elif 'ranking_type' in task.keys():
                        task_obj = database.Task.objects(data=str(data_obj._id),
                                                         ranking_type=task['ranking_type']).first()
                        if not task_obj:
                            task_obj = database.Task()
                            task_obj = add_fields_from_data(list(task.keys()), list(task.values()), task_obj)
                            task_obj.ranking_type = task['ranking_type']
                    elif 'ranking_type_2' in task.keys():
                        task_obj = database.TaskCompare.objects(data=str(data_obj._id),
                                                                ranking_type_1=task['ranking_type_1'],
                                                                ranking_type_2=task['ranking_type_2']).first()
                        if not task_obj:
                            task_obj = database.TaskCompare()
                            task_obj = add_fields_from_data(list(task.keys()), list(task.values()), task_obj)
                            task_obj.ranking_type_1 = task['ranking_type_1']
                            task_obj.ranking_type_2 = task['ranking_type_2']

                    task_obj.data = str(data_obj._id)
                    task_obj.save()

                    if not exp_obj or (
                            not str(task_obj.auto_id_0) in exp_obj.tasks or not str(task_obj._id) in exp_obj.tasks):
                        tasks_obj.append(str(task_obj.auto_id_0))

        if exp_obj:
            if len(tasks_obj) > 0:
                exp_obj.tasks.extend(tasks_obj)
        else:
            if not exp_obj and tasks_obj is not None:
                exp_obj = database.Experiment(_exp_id=str(exp_info['exp_id']), _description=exp_info['description'],
                                              tasks=tasks_obj)
        exp_obj.save()


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


def add_data_to_db(data, fields, ranking_type, query_col, sort_col='score', ascending=False):
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
