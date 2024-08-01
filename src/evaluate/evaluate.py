import json

import numpy as np
import pandas as pd
import pytrec_eval

import database

from evaluate.fairness_metrics import selection_parity, parity_of_exposer, compute_igf_ratio


def get_fairness_metrics(configs, docs_obj):
    """Generates fairness metrics based on the dataset sensitive features.

    Args:
        configs (object): Config object for specific dataset.
        docs_obj (object): Document object for fairness evaluation representing a ranking for a specific query.

    Returns:
        dict: Dictionary containing fairness metrics.
    """
    results = dict()

    orig_df = pd.concat([pd.json_normalize(json.loads(doc.to_json())) for doc in docs_obj])
    df_top = orig_df[:configs["ui_display_config"]["display_metrics"]["top_k"]]
    for metric in configs["ui_display_config"]["display_metrics"]["fairness_metrics"]:
        if metric == 'selection_parity':
            result = selection_parity(df_top, orig_df, configs["data_reader_class"]["group"])
        elif metric == 'exposer_parity':
            result = parity_of_exposer(df_top, configs["data_reader_class"]["group"], orig_df[configs["data_reader_class"]["group"]].unique())
        elif metric == 'igf':
            result = compute_igf_ratio(df_top, orig_df, configs["data_reader_class"]["group"], configs["data_reader_class"]["score"], configs["data_reader_class"]["docID"])
        results[metric.replace('_', ' ')] = result
    return results


def get_utility_metrics(configs, docs_obj):
    """Generates utility metrics on measuring the matching degree between a query and document objects.

    Args:
        configs (object): Config object for specific dataset.
        docs_obj (object): Document object for fairness evaluation representing a ranking for a specific query.

    Returns:
        dict: Dictionary containing utility metrics.
    """
    qrel = dict()
    run = dict()

    qrel["current_query"] = dict()
    run["current_query"] = dict()

    docs_original = sorted(docs_obj, key=lambda x: x[configs["data_reader_class"]["score"]], reverse=True)
    top_k_docs_orig = docs_original[:configs["ui_display_config"]["display_metrics"]["top_k"]]
    top_k_docs = docs_obj[:configs["ui_display_config"]["display_metrics"]["top_k"]]

    rel = len(top_k_docs_orig)
    for doc in top_k_docs_orig:
        qrel["current_query"][str(doc._id)] = rel
        rel = rel - 1

    rel = len(top_k_docs_orig)
    for doc in top_k_docs:
        run["current_query"][str(doc._id)] = rel
        rel = rel - 1

    evaluator = pytrec_eval.RelevanceEvaluator(
        qrel, configs["ui_display_config"]["display_metrics"]["utility_metrics"])

    results_eval = evaluator.evaluate(run)
    results = dict()
    for metric in results_eval["current_query"]:
        results[metric.upper()] = np.round(results_eval["current_query"][metric], 2)
    return results


def get_average_interactions(experiment_id, interaction="n_views"):
    """Generates average interaction for an experiment.

    Args:
        experiment_id (string): Experiment ID for which to compute the average.
        interaction (string): Interaction type for which to compute the average.

    Returns:
        dict: Dictionary containing average interactions per ranking type.
    """
    users = database.User.objects(tasks_visited__exp=str(experiment_id))
    exp_obj = database.Experiment.objects(_exp_id=str(experiment_id)).first()

    avg_interactions = dict()
    for user in users:
        for task_vis in user.tasks_visited:
            if task_vis.exp == str(experiment_id):
                task_obj = database.Task.objects(_id=exp_obj.tasks[int(task_vis.task)]).first()
                data_obj = database.Data.objects(_id=task_obj.data).first()
                doc_ids = [ranking for ranking in data_obj.rankings if ranking.ranking_type == task_obj.ranking_type][0].docs
                for index, doc in enumerate(doc_ids):
                    if doc not in avg_interactions:
                        avg_interactions[str(doc) + '__' + task_obj.ranking_type] = 0
                    avg_interactions[str(doc) + '__' + task_obj.ranking_type] = avg_interactions[str(doc) + '__' + task_obj.ranking_type] + \
                                                                                + float(task_vis.interactions[index][interaction])

    for key in avg_interactions.keys():
        avg_interactions[key] = avg_interactions[key] / len(users)

    return avg_interactions

