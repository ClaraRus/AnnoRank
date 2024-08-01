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
