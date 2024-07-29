import os


class Ranker:
    def __init__(self, configs, data_configs, model_path):
        """Define your own ranker.
        """
        self.configs = configs
        self.data_configs = data_configs
        self.model_path = os.path.join(model_path, self.configs['ranking_type'])

    def train_model(self, data_train, data_test, experiment):
        pass

    def predict(self, data, experiment):
        pass