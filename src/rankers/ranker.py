import os


class Ranker:
    """
        Ranker class.
    """
    def __init__(self, configs, data_configs, model_path):
        """
        Ranker init class.
        Attributes
        ----------
        configs : dict
            configuration dict of the ranker
        data_configs : dict
            configuration dict of the dataset
        model_path : str
            path to the output file where the model and predictions will be saved
        """
        self.configs = configs
        self.data_configs = data_configs
        self.model_path = os.path.join(model_path, self.configs['ranking_type'])

    def train_model(self, data_train, data_test, experiment):
        """Train the ranking model.
        The train method should save the trained model at the following path:
        self.model_path/<train_ranking_type>__<test_ranking_ type>.
        Args:
            data_train (pandas.Dataframe): Data to be used for training
            data_test (pandas.Dataframe): Data to be used for testing
            experiment (tuple): Tuple containing the <train_ranking_type> and <test_ranking_type> defined
            in the configuration file.
        """
        pass

    def predict(self, data, experiment):
        """
        Append to the data the predicted score by the ranking model.
        Args:
            data (pandas.Dataframe): Data to be used for training.
            experiment (tuple): Tuple containing the <train_ranking_type> and <test_ranking_type> defined
            in the configuration file.
        Returns:
            predictions (pandas.Dataframe): Data containing an appended column representing the predicted score.
            The column with the predicted score should follow the convention <train_score_column>__<test_score_column>.
            For example if the <train_ranking_type> and <test_ranking_type> is set to be “original”,
            the predicted score column should be ”score”__”score”.
            If the train and test data are pre-processed by a fairness intervention the predicted score column
            should be ”score”_fair__”score”_fair, where “score” is the value defined
            in the config file under the “score” field.
        """
        pass