import json
import os
from pathlib import Path

import pandas as pd

project_dir = Path.cwd()


class DataReader():
    """
    DataReader class for reading pre-determined dataset and data transformation for the UI. 
    """
    
    def __init__(self, configs):
        """
        Data reader init class.
        Attributes
        ----------
        name : str
            name of the dataset set in run_apps args
        query_col : str
            query column
        sensitive_col : str
            sensitive features for ranking process
        data_path : str
            path to the dataset file
        output_file_path : str
            path to the output file
        """
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
        """Read dataset file and read it into Pandas dataframe for further processing.

        Args:
            split (str): The split of the dataset to read ('test' or 'train').

        Returns:
            If split is 'test':
                tuple: A tuple containing the dataframes of document, query, and experiment lists.
            If split is 'train':
                tuple: A tuple containing the dataframes of document and query.

        Raises:
            FileNotFoundError: If the dataset file or query file is not found.

        """
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
        """Save data based on the splits category and after the dataset transformation process.

        This method creates the necessary directories and saves the transformed data to CSV files.
        The data is saved in the following structure:
        - The main output directory is created at `self.output_file_path`.
        - Inside the main output directory, two subdirectories are created: 'test' and 'train'.
        - The transformed test data is saved as 'data.csv' inside the 'test' subdirectory.
        - If there is transformed train data available, it is saved as 'data.csv' inside the 'train' subdirectory.
        - The dataset queries are saved as 'query.csv' inside the main output directory.

        Note: The method assumes that the necessary data has already been transformed and is available.

        Returns:
            None
        """
        os.makedirs(self.output_file_path)
        dataset_queries, data_train, data_test = self.transform_data()
        os.makedirs(os.path.join(self.output_file_path, 'test'))
        os.makedirs(os.path.join(self.output_file_path, 'train'))
        data_test.to_csv(os.path.join(self.output_file_path, 'test', 'data.csv'), index=False)
        if data_train is not None:
            data_train.to_csv(os.path.join(self.output_file_path, 'train', 'data.csv'), index=False)
        dataset_queries.to_csv(os.path.join(self.output_file_path, 'query.csv'), index=False)
