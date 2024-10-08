import os
from pathlib import Path

import pandas as pd

from utils.utils import writeToTXT, check_nan, get_ltr_cols


def generate_ranklib_data(data_train, data_test, model_path, experiment, configs, data_configs):
    """
        Generates RankLib formatted data files.

        Args:
            data_train (pandas.DataFrame): Training dataset.
            data_test (pandas.DataFrame): Testing dataset.
            model_path (str): Path to save the model and data files.
            experiment (tuple): Tuple containing the <train_ranking_type> and <test_ranking_type> defined
            in the configuration file.
            configs (dict): Configuration dict of the ranker.
            data_configs (dict): Configuration dict of the dataset.

        Returns:
            None
    """
    if 'Unnamed: 0' in data_train:
        data_train = data_train.drop(['Unnamed: 0'], axis=1)

    if 'Unnamed: 0' in data_test:
        data_test = data_test.drop(['Unnamed: 0'], axis=1)


    out_dir = os.path.join(model_path, experiment[0] + '__' + experiment[1])
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

        cols_train = get_ltr_cols(configs['features'], data_configs['score'], "original" not in experiment[0])
        cols_test = get_ltr_cols(configs['features'], data_configs['score'], "original" not in experiment[1])

        if check_nan(data_train, cols_train):
            raise ValueError('Nan values in train!')
        if check_nan(data_test, cols_test):
            raise ValueError('Nan values in test!')

        data_train = data_train.sort_values(data_configs['query'])
        data_test = data_test.sort_values(data_configs['query'])

        df_train = data_train.copy()
        df_train = assign_judgements(df_train, data_configs['query'], cols_train[-1], configs['pos_th'])
        df_train[data_configs['query']] = df_train[data_configs['query']].astype('category').cat.codes
        df_train_ranklib = create_ranklib_data(df_train, data_configs, cols_train)

        df_test = data_test.copy()
        df_test = assign_judgements(df_test, data_configs['query'], cols_test[-1],configs['pos_th'])
        df_test[data_configs['query']] = df_test[data_configs['query']].astype('category').cat.codes
        df_test_ranklib = create_ranklib_data(df_test, data_configs, cols_test)

        output_f = os.path.join(out_dir, "train_ranklib.txt")
        writeToTXT(output_f, df_train_ranklib)

        output_f = os.path.join(out_dir, "test_ranklib.txt")
        writeToTXT(output_f, df_test_ranklib)
        print("--- Save ranklib data in", output_f, " --- \n")


def create_ranklib_data(df_copy, data_configs, cols_train):
    """
        Converts a DataFrame to RankLib format.

        Args:
            df_copy (DataFrame): DataFrame to convert.
            data_configs (dict): Configuration dict of the dataset.
            cols_train (list): List of column names to keep for the model to use durign training.

        Returns:
            DataFrame: DataFrame in RankLib format.
    """
    idx = 0
    cols_keep = []

    for ci in cols_train[:-1]:
        cols_keep.append(ci)
        df_copy[ci] = df_copy[ci].apply(lambda x: str(idx + 1) + ":" + str(round(x, 4)))
        idx = idx + 1

    df_copy["query"] = df_copy[data_configs["query"]].apply(lambda x: "qid:" + str(x))
    df_copy = df_copy.sort_values(data_configs["docID"])
    df_copy['docID'] = df_copy[data_configs["docID"]].astype('category').cat.codes
    df_copy["comment"] = df_copy[["docID", "judgement", cols_train[-1]]].astype(str).apply(
        lambda x: ("#docid={};rel={};" + "score={};").format(x.iloc[0], x.iloc[1], x.iloc[2]),
        axis=1)

    # shuffle df test
    groups = [df_copy for _, df_copy in df_copy.groupby('query')]
    shuffled_groups = [gr.sample(frac=1) for gr in groups]
    df_copy = pd.concat(shuffled_groups).reset_index(drop=True)

    df_copy = df_copy[["judgement", "query"] + cols_keep + ["comment"]]

    return df_copy


def add_judgement(x, score_col, th):
    """
        Assigns judgement values based on the score column and threshold.

        Args:
            x (Series): Series of data.
            score_col (str): Name of the score column.
            th (float): Threshold value for judging relevance.

        Returns:
            Series: Series with judgement values added.
    """
    x['judgement'] = x[score_col].apply(lambda x: round(x, 2) if round(x, 2) > th else 0)
    return x


def assign_judgements(df, query_col, score_col, th):
    """
        Assigns judgements to the DataFrame based on the score column and threshold.

        Args:
            df (DataFrame): DataFrame to process.
            query_col (str): Name of the query column.
            score_col (str): Name of the score column.
            th (float): Threshold value for judging relevance.

        Returns:
            DataFrame: DataFrame with judgements assigned.
    """
    df = df.groupby([query_col]).apply(lambda x: x.sort_values(by=score_col, ascending=False)).reset_index(
        drop=True)
    temp = df.groupby([query_col]).apply(
        lambda x: add_judgement(x, score_col, th))
    df = temp.reset_index(drop=True)

    return df
