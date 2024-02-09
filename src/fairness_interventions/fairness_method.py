import os


class FairnessMethod():
    def __init__(self, configs, data_configs, model_path):
        self.configs = configs
        self.data_configs = data_configs

        if model_path is None:
            self.model_path = ""
        else:
            self.model_path = os.path.join(model_path, configs['ranking_type'])


    def generate_fair_data(self, data):
        return data

    def train_model(self, data_train):
        pass