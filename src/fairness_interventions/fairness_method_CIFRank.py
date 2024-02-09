import os
from pathlib import Path
import pandas as pd

from src.fairness_interventions.fairness_method import FairnessMethod
from src.fairness_interventions.modules.CIFRank_module.generate_counterfactual_data import get_counterfactual_data_real

project_dir = Path.cwd()


class CIFRank(FairnessMethod):
    def __init__(self, configs, data_configs, model_path):
        super().__init__(configs, data_configs, model_path)

    def train_model(self, data_train):
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
            self.run_causal_model(data_train)

    def generate_fair_data(self, data):
        counter_data = self.generate_counterfactual_data(data)

        return counter_data

    def run_causal_model(self, data):
        from rpy2 import robjects
        from rpy2.robjects import pandas2ri

        qids = data[self.data_configs['query']].unique()
        for qid in qids:
            temp = data[data[self.data_configs['query']] == qid].copy()
            temp = temp[temp[self.data_configs['score']] > self.configs['pos_th']]
            temp = temp[[self.data_configs['query'], self.data_configs['docID'], self.data_configs['group'],
                         self.data_configs['score']] + self.configs['features']]
            try:
                pandas2ri.activate()
                r = robjects.r
                r_script = "./src/fairness_interventions/modules/CIFRank_module/R/estimate_causal_model.R"
                r.source(r_script, encoding="utf-8")
                r.estimate_causal_model(temp, self.data_configs['group'], self.data_configs['score'],
                                        self.configs['features'], self.configs['control'],
                                        os.path.join(self.model_path, str(qid)))
            except:
                if len(os.listdir(self.model_path)) != 0:
                    df = pd.DataFrame(columns=["Mediators"])
                    df["Mediators"] = 'nan'
                    df.to_csv(os.path.join(self.model_path, 'identified_mediators.csv'))

            self.save_med_results(temp, os.path.join(self.model_path, str(qid)))

    def generate_counterfactual_data(self, data):
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

    def save_med_results(self, temp, out_path):
        if os.path.exists(os.path.join(out_path, 'med_output.txt')):
            with open(os.path.join(out_path, 'med_output.txt'), 'r') as f:
                content = f.readlines()
            results_dict = dict()
            next_indirect = False
            for line in content:
                line = line.strip()
                if line.startswith('For the predictor'):
                    if len(results_dict.keys()) == 0:
                        pred = line.split(' ')[3]
                        df_med = pd.DataFrame(columns=['Metric', 'Estimate'])
                        results_dict[pred] = ''
                    else:
                        results_dict[pred] = df_med
                        pred = line.split(' ')[3]
                        df_med = pd.DataFrame(columns=['Metric', 'Estimate'])

                if line.startswith('The estimated total effect:'):
                    total_effect = float(line.split(' ')[4])
                    temp_df = pd.DataFrame([['Total Effect', total_effect]], columns=['Metric', 'Estimate'])
                    df_med = pd.concat([df_med, temp_df], ignore_index=True)

                if next_indirect:
                    splits = line.split(' ')
                    if splits[0] == '':
                        indirect_effect = float(line.split(' ')[1])
                    else:
                        indirect_effect = float(line.split(' ')[0])
                    temp_df = pd.DataFrame([['Indirect Effect', indirect_effect]], columns=['Metric', 'Estimate'])
                    df_med = pd.concat([df_med, temp_df], ignore_index=True)
                    next_indirect = False

                if line.startswith('y1.all'):
                    next_indirect = True

            results_dict[pred] = df_med

            pred_groups = [p.split('pred')[1] for p in results_dict.keys()]
            groups = temp[self.data_configs['group']].unique()
            pred_gr = [g for g in groups if g not in pred_groups and g != self.configs['control']][0]

            index = 0
            for key in results_dict.keys():
                index = index + 1
                df_med = results_dict[key]
                direct_effect = df_med[df_med['Metric'] == 'Total Effect']['Estimate'].values[0] - \
                                df_med[df_med['Metric'] == 'Indirect Effect']['Estimate'].values[0]
                temp_df = pd.DataFrame([['Direct Effect', direct_effect]], columns=['Metric', 'Estimate'])
                df_med = pd.concat([df_med, temp_df], ignore_index=True)

                if key == 'pred' or key == '':
                    file_name = pred_gr + '_med.csv'
                elif 'pred.temp1$x' in key:
                    file_name = groups[index] + '_med.csv'
                else:
                    file_name = key.split('pred')[1] + '_med.csv'

                df_med.to_csv(os.path.join(out_path, file_name))
