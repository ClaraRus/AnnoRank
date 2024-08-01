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

import os


class FairnessMethod():
    def __init__(self, configs, data_configs, model_path):
        """
        FairnessMethod init class.
        Attributes
        ----------
        configs : dict
            configuration dict of the fairness method
        data_configs : dict
            configuration dict of the dataset
        model_path : str
            path to the output file where the model and predictions will be saved
        """
        self.configs = configs
        self.data_configs = data_configs

        if model_path is None:
            self.model_path = ""
        else:
            self.model_path = os.path.join(model_path, configs['ranking_type'])

    def generate_fair_data(self, data):
        """Generate the fair data by appending the new fair columns to the data.
        Fair columns are added following the name convention <column_name>_fair.

        Args:
            data (pandas.Dataframe): dataset to apply the fairness method
        Returns:
            data (pandas.Dataframe): dataset containing the transformed columns
        """
        return data

    def train_model(self, data_train):
        """Train model

        Args:
            data_train (pandas.Dataframe): train dataset
            The train_model method should save the fairness intervention method to self.model_path.
        """
        pass
