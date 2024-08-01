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

import json
import os
import subprocess
import sys

import pandas as pd

from fairness_interventions.fairness_method import FairnessMethod


def conda_activate(env_name):
    # due to conflicting versions FA*IR needs a different conda env activated
    activate_cmd = "cd /opt/conda/ && . activate " + env_name
    subprocess.run(activate_cmd, shell=True)
class FAIRRanking(FairnessMethod):
    def __init__(self, configs, data_configs, model_path):
        super().__init__(configs, data_configs, model_path=None)

    def generate_fair_data(self, data):
        """Generate the fair data by appending the new fair columns to the data.
        Fair columns are added following the name convention <column_name>_fair.

        Args:
            data (pandas.Dataframe): dataset to apply the fairness method
        Returns:
            data (pandas.Dataframe): dataset containing the transformed columns
        """
        temp_dir = "/app/src/fairness_interventions/modules/FAIR_module/temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        data.to_csv(os.path.join(temp_dir, "data_test.csv"))

        with open(os.path.join(temp_dir, "config.json"), 'w') as file:
            json.dump(self.configs, file, indent=4)

        with open(os.path.join(temp_dir, "data_configs.json"), 'w') as file:
            json.dump(self.data_configs, file, indent=4)

        result = subprocess.run("conda env list", shell=True, capture_output=True, text=True)

        yml_file_path = False
        if "fair" not in result.stdout:
            # Specify the path to your environment.yml file
            yml_file_path = "/app/src/fairness_interventions/modules/FAIR_module/env_fair.yml"

        run_cmd = ""
        if yml_file_path:
            run_cmd = "conda env create -f " + yml_file_path + " && "

        run_cmd = run_cmd + "conda run -n fair python /app/src/fairness_interventions/modules/FAIR_module/FAIR_generate.py --config " + \
                       os.path.join(temp_dir, "config.json") + " --data_configs " + os.path.join(temp_dir, "data_configs.json") + \
                        " --data_test " + os.path.join(temp_dir, "data_test.csv")
        result = subprocess.run(run_cmd, shell=True, capture_output=True, text=True)
        predictions = pd.read_csv(os.path.join(temp_dir, "re_ranked.csv"))
        return predictions

