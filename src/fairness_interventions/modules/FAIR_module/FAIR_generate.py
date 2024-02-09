import argparse
import json
import os


from fairsearchcore.models import FairScoreDoc
from fairsearchcore import Fair
import pandas as pd


def doc_to_df(docs, data_test, data_configs):
    predictions = []
    rank = 1

    for doc in docs:
        temp_df = data_test[data_test[data_configs['docID']] == doc.id]
        temp_df.loc[:,'rank_fair'] = [rank]
        rank = rank + 1
        predictions.append(temp_df)

    predictions = pd.concat(predictions)
    mask = data_test[data_configs['query']] == predictions[data_configs['query']].unique()[0]
    data_test_qid = data_test[mask]
    if len(predictions) != len(data_test_qid):
        mask = data_test_qid[data_configs['docID']].apply(
            lambda x: x not in predictions[data_configs['docID']].values)
        data_test_qid_add = data_test_qid[mask]
        data_test_qid_add.sort_values(data_test_qid.columns[-1])
        data_test_qid_add.loc[:,'rank_fair'] = list(range(rank, len(data_test_qid)+1))
        predictions = pd.concat([predictions, data_test_qid_add])
    return predictions


def format_data(re_ranked_list, data_test, data_configs):
    predictions = []

    for ranked_list in re_ranked_list:
        predictions.append(doc_to_df(ranked_list, data_test, data_configs))
    predictions = pd.concat(predictions)
    return predictions


def check_is_protected(x, data, k, data_configs):
    s_value = x[data_configs['group']]
    diversity_k = sum((data.head(k)[data_configs['group']] == s_value).values)
    th_diversity = k / len(data[data_configs['group']].unique())

    if diversity_k > th_diversity:
        return False
    else:
        return True


def init_FairDocs(data, k, data_configs):
    docs = []
    score_col = data.columns[-1]
    for _, x in data.iterrows():
        docs.append(FairScoreDoc(x[data_configs['docID']], x[score_col], check_is_protected(x, data, k, data_configs)))
    return docs


def generate(data_test, configs, data_configs):
    temp_dir = "/app/src/fairness_interventions/modules/FAIR_module/temp"

    p = configs[
        'p']  # proportion of protected candidates in the topK elements (value should be between 0.02 and 0.98)
    alpha = configs['alpha']  # significance level (value should be between 0.01 and 0.15)
    k = configs['k']

    data_test = data_test.groupby(data_configs['query']).apply(
        lambda x: x.sort_values(data_test.columns[-1], ascending=False)).reset_index(drop=True)
    unfair_ranking_qids = data_test.groupby(data_configs['query']).apply(
        lambda x: init_FairDocs(x, len(data_test), data_configs))

    re_ranked_list = []
    for unfair_ranking_qid in unfair_ranking_qids:
        # create the Fair object
        fair = Fair(k, p, alpha)

        # now re-rank the unfair ranking
        re_ranked = fair.re_rank(unfair_ranking_qid)
        if isinstance(re_ranked[0], list):
            re_ranked_list.append(re_ranked[0] + re_ranked[1])
        else:
            re_ranked_list.append(re_ranked)
    predictions = format_data(re_ranked_list, data_test, data_configs)
    predictions.to_csv(os.path.join(temp_dir, "re_ranked.csv"))


parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, help='Path to config file')
parser.add_argument('--data_configs', required=True, help='Path to data_test file')
parser.add_argument('--data_test', required=True, help='Path to data_test file')

args = parser.parse_args()

with open(args.config, 'r') as file:
    configs = json.load(file)
with open(args.data_configs, 'r') as file:
    data_configs = json.load(file)

data_test = pd.read_csv(args.data_test)
generate(data_test, configs, data_configs)
