import os
import pickle
from pathlib import Path

import pandas as pd
from sklearn import preprocessing

from src.fairness_interventions.modules.DELTR.fairsearchdeltr import Deltr
from src.fairness_interventions.fairness_method import FairnessMethod
from src.ranklib.generate_ranklib_data import assign_judgements

project_dir = Path.cwd()


class DELTR(FairnessMethod):
    def __init__(self, configs, data_configs, model_path):
        super().__init__(configs=configs, data_configs=data_configs, model_path=model_path)

    def generate_fair_data(self, data_train, data_test):
        return data_train, data_test

    def format_data(self, data, columns_train):
        data = assign_judgements(data, columns_train, self.data_configs['query'], columns_train[-1], self.configs['pos_th'])
        new_data = pd.DataFrame()
        new_data['q_id'] = data[self.data_configs['query']]
        new_data['doc_id'] = data[self.data_configs['docID']]

        label_encoder = preprocessing.LabelEncoder()
        new_data[self.data_configs['group']] = label_encoder.fit_transform(
            data[self.data_configs['group']])

        for col in columns_train:
            new_data[col] = data[col]

        new_data['judgement'] = data['judgement']

        return new_data

    def train_model(self, data):
        columns = data.columns
        new_data = self.format_data(data, columns)

        if not os.path.exists(os.path.join(self.model_path, 'model_fair.sav')):
                self.train_model_deltr(new_data)

    def train_model_deltr(self, data):
        dtr = Deltr(self.data_configs['group'], self.configs['gamma'],
                    self.configs['iterations'], standardize=True)
        # train the model
        model = dtr.train(data)
        filename = 'model_fair.sav'

        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)

        pickle.dump(model, open(os.path.join(self.model_path, filename), 'wb'))
        # save model
        logs = dtr.log
        # save logs
        with open(os.path.join(self.model_path, 'log.txt'), 'w') as f:
            f.write(str(logs))

    def generate_predictions(self, data):
        # load model
        filename = 'model_fair.sav'
        _omega = pickle.load(open(os.path.join(self.model_path, filename), 'rb'))
        dtr = Deltr(self.data_configs['group'], self.configs['gamma'],
                    self.configs['iterations'], standardize=False)
        dtr._omega = _omega

        # generate predictions
        label_encoder = preprocessing.LabelEncoder()
        data[self.data_configs['group']] = label_encoder.fit_transform(
            data[self.data_configs['group']])
        predictions = dtr.rank(data)

        data = pd.merge(data, predictions, on=self.data_configs['query'])
        data = data.sort_values(by=[self.data_configs['query'], 'judgement'])

        def convert_rank(x, experiment_string):
            x = x.sort_values(by=['judgement'])
            x[experiment_string] = list(range(1, len(x) + 1))

            return x

        experiment_string = "rank_fair"
        data = data.groupby(self.data_configs['query']).apply(lambda x: convert_rank(x, experiment_string)).reset_index(drop=True)

        return data
