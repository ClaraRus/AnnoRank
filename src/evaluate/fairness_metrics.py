import math
from collections import Counter

import numpy as np
import pandas as pd
from numpy import mean


def parity_of_exposer(top_df, group_col, s_values):
    """
    Calculate the parity of exposer metric.

    Args:
        top_df (pandas.DataFrame): DataFrame containing the top-ranked items.
        group_col (str): Name of the column representing the groups.
        s_values (list): List of group values.

    Returns:
        float: Parity of exposer metric value.
    """
    rank = len(top_df)
    ranks = []
    for index in range(len(top_df)):
        ranks.append(rank)
        rank = rank - 1
    top_df['rank'] = ranks
    top_df['exposer'] = top_df['rank'].apply(lambda x:  1 / math.log2(x + 1))
    exposer = top_df.groupby(group_col).apply(lambda gr: mean(gr['exposer']))
    res = 0

    for gr in s_values:
        if gr in exposer:
            res = abs(res - exposer[gr])
    return np.round(abs(res), 2)


def selection_parity(top_df, orig_df,  group_col):
    """
    Calculate the selection parity metric.

    Args:
        top_df (pandas.DataFrame): DataFrame containing the top-ranked items.
        orig_df (pandas.DataFrame): DataFrame containing the original items.
        group_col (str): Name of the column representing the groups.

    Returns:
        float: Selection parity metric value.
    """
    top_counts = top_df[group_col].value_counts() / len(top_df)
    orig_counts = orig_df[group_col].value_counts() / len(orig_df)
    result = top_counts - orig_counts
    res_value = 0
    for gr in orig_df[group_col].unique():
        res_value = abs(res_value - result[gr])
    return np.round(res_value, 2)


def compute_igf_ratio(top_df, orig_df, group_col, orig_sort_col, id_col):
    """
    Calculate the IGF (Item Group Fairness) ratio.

    Args:
        top_df (pandas.DataFrame): DataFrame containing the top-ranked items.
        orig_df (pandas.DataFrame): DataFrame containing the original items.
        group_col (str): Name of the column representing the groups.
        orig_sort_col (str): Name of the column used for sorting the original items.
        id_col (str): Name of the column representing the item IDs.

    Returns:
        str: IGF ratio for each group in the format "GROUP: RATIO, GROUP: RATIO, ...".
    """
    # assume _orig_df is sorted according to the _orig_sort_col
    cur_res = dict()
    for group in orig_df[group_col].unique():
        group_orig = orig_df[orig_df[group_col] == group]
        group_top = top_df[top_df[group_col] == group]

        top_k_IDS = group_top[id_col]

        if len(group_orig[~group_orig[id_col].isin(top_k_IDS)]) == 0:
            igf = 1
        elif len(group_orig[group_orig[id_col].isin(top_k_IDS)]) == 0:
            igf = 0
        else:
            igf = min(group_orig[group_orig[id_col].isin(top_k_IDS)][orig_sort_col]) / max(
                group_orig[~group_orig[id_col].isin(top_k_IDS)][orig_sort_col])

        if igf > 1:
            cur_res[group] = 1
        else:
            cur_res[group] = igf

    str_res = ""
    for group in sorted(orig_df[group_col].unique()):
        str_res = str_res + group.upper() + ":" + str(np.round(cur_res[group], 2)) + ", "

    str_res = str_res.strip(", ")
    return str_res
