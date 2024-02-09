import os
import subprocess
from pathlib import Path
from src.rankers.ranker import Ranker

from src.rankers.modules.ranklib.generate_predictions import get_LTR_predict
from src.rankers.modules.ranklib.generate_ranklib_data import generate_ranklib_data

project_dir = Path.cwd()

java_bin_path = '/opt/java/jdk-15.0.2/bin'
# Get the current PATH variable
current_path = os.environ.get('PATH', '')
# Append the Java bin path to the PATH variable
new_path = f'{current_path}:{java_bin_path}'
# Update the PATH environment variable
os.environ['PATH'] = new_path

class RankLibRanker(Ranker):
    def __init__(self, configs, data_configs, model_path):
        super().__init__(configs, data_configs, model_path)

        if not os.path.exists("/opt/java"):
            install_java_command = "mkdir /opt/java && cd /opt/java && \
                                          wget https://download.java.net/java/GA/jdk15.0.2/0d1cfde4252546c6931946de8db48ee2/7/GPL/openjdk-15.0.2_linux-x64_bin.tar.gz && cd /opt/java && tar -zxvf openjdk-15.0.2_linux-x64_bin.tar.gz"
            subprocess.run(install_java_command, shell=True, capture_output=True, text=True)

        self.args = [os.path.join(project_dir, "src", "rankers", "modules/ranklib"), self.configs['metric'],
                     self.configs['top_k'], self.configs['rel_max'],
                     self.configs['ranker'], self.configs['ranker_id'],
                     self.configs['lr'], self.configs['epochs']]

    def train_model(self, data_train, data_test, experiment):
        install_java_command = "mkdir /opt/java && cd /opt/java && \
                              wget https://download.java.net/java/GA/jdk15.0.2/0d1cfde4252546c6931946de8db48ee2/7/GPL/openjdk-15.0.2_linux-x64_bin.tar.gz && cd /opt/java && tar -zxvf openjdk-15.0.2_linux-x64_bin.tar.gz"
        subprocess.run(install_java_command, shell=True, capture_output=True, text=True)

        generate_ranklib_data(data_train, data_test, self.model_path, experiment, self.configs, self.data_configs)

        exp_string = experiment[0] + '__' + experiment[1]
        if not os.path.exists(
                os.path.join(self.model_path, exp_string, 'ranklib-experiments', self.configs['ranker'])):
            subprocess.check_call(
                [os.path.join(project_dir, "src", "rankers", "modules", "ranklib", "run-LTR-model.sh"), self.args[0],
                 str(self.args[1]),
                 str(self.args[2]), str(self.args[3]), str(self.args[4]), str(self.args[5]), os.path.join(self.model_path, exp_string),
                 str(self.args[6]),
                 str(self.args[7])])


    def predict(self, data, experiment):
        data = data.sort_values(self.data_configs['query'])
        predictions = get_LTR_predict(data, self.model_path, self.configs['ranker'], experiment,
                                      self.data_configs, self.configs['features'])
        return predictions

