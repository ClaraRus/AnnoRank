import json
import os
from pathlib import Path

import pandas as pd

project_dir = Path.cwd()


class DataReader():

    def __init__(self, configs):
        self.name = configs["name"]
        self.query_col = configs["query"]
        self.sensitive_col = configs["group"]
        self.score_col = configs["score"]

        self.data_path = os.path.join(
            project_dir, 'dataset/' + self.name)
        self.output_file_path = os.path.join(self.data_path, 'format_data')
        if not os.path.exists(self.output_file_path):
            self.save_data()

    def read(self, split):
        dataframe_data = pd.read_csv(os.path.join(self.output_file_path, split, 'data.csv'))
        dataframe_query = pd.read_csv(os.path.join(self.output_file_path, 'query.csv'))

        if split == 'test':
            experiments_files = [file for file in os.listdir(os.path.join(self.data_path, 'experiments')) if
                                 file.endswith('.json')]
            experiments_info = []
            for exp_file in experiments_files:
                with open(os.path.join(self.data_path, 'experiments', exp_file)) as f:
                    exp_info = json.load(f)
                    experiments_info.append(exp_info)


            return dataframe_data, dataframe_query, experiments_info
        else:
            return dataframe_data, dataframe_query

    def save_data(self):
        os.makedirs(self.output_file_path)
        dataset_queries, data_train, data_test = self.transform_data()
        os.makedirs(os.path.join(self.output_file_path, 'test'))
        os.makedirs(os.path.join(self.output_file_path, 'train'))
        data_test.to_csv(os.path.join(self.output_file_path, 'test', 'data.csv'), index=False)
        if data_train is not None:
            data_train.to_csv(os.path.join(self.output_file_path, 'train', 'data.csv'), index=False)
        dataset_queries.to_csv(os.path.join(self.output_file_path, 'query.csv'), index=False)
