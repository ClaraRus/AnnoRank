import os
from pathlib import Path
import pandas as pd

from fairness_interventions.fairness_method import FairnessMethod
from fairness_interventions.modules.CIFRank_module.generate_counterfactual_data import get_counterfactual_data_real
from fairness_interventions.modules.CIFRank_module.run_causal_model import run_causal_model

project_dir = Path.cwd()


class CIFRank(FairnessMethod):
    def __init__(self, configs, data_configs, model_path):
        super().__init__(configs, data_configs, model_path)

    def train_model(self, data_train):
        """Train model

        Args:
            data_train (pandas.Dataframe): train dataset
            The train_model method should save the fairness intervention method to self.model_path.
        """
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
            run_causal_model(data_train, self.model_path, self.configs, self.data_configs)

    def generate_fair_data(self, data):
        """Generate the fair data by appending the new fair columns to the data.
        Fair columns are added following the name convention <column_name>_fair.

        Args:
            data (pandas.Dataframe): dataset to apply the fairness method
        Returns:
            data (pandas.Dataframe): dataset containing the transformed columns
        """
        counter_data = self.generate_counterfactual_data(data)

        return counter_data


    def generate_counterfactual_data(self, data):
        """Generates the fair data by using the causal estimates
        Args:
            data (pandas.Dataframe): data on which to append the fair columns

        Returns:
            data (pandas.Dataframe): data containing the appended fair columns which contain
            the counterfactual values computed based on the causal estimates
        """
        qids = data[self.data_configs['query']].unique()
        count_dfs = []
        for qid in qids:
            qid_df = data[data[self.data_configs['query']] == qid]

            qid_path_causal = os.path.join(self.model_path, str(qid))
            if os.path.exists(qid_path_causal):
                if len(os.listdir(qid_path_causal)):
                    qid_fair_df = get_counterfactual_data_real(qid_df, qid_path_causal, self.configs, self.data_configs)
                    count_dfs.append(qid_fair_df)
        final_df = pd.concat(count_dfs)

        return final_df

