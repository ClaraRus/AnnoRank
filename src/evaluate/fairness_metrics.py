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

import math
from collections import Counter

import numpy as np
import pandas as pd
from numpy import mean


def parity_of_exposer(df_top, group_col, s_values):
    """
    Calculate the parity of exposer metric.

    Args:
        df_top (pandas.DataFrame): DataFrame containing the top-ranked items.
        group_col (str): Name of the column representing the groups.
        s_values (list): List of group values.

    Returns:
        float: Parity of exposer metric value.
    """
    rank = len(df_top)
    ranks = []
    for index in range(len(df_top)):
        ranks.append(rank)
        rank = rank - 1
    df_top['rank'] = ranks
    df_top['exposer'] = df_top['rank'].apply(lambda x:  1 / math.log2(x + 1))
    exposer = df_top.groupby(group_col).apply(lambda gr: mean(gr['exposer']))
    res = 0

    for gr in s_values:
        if gr in exposer:
            res = abs(res - exposer[gr])
    return np.round(abs(res), 2)


def selection_parity(_top_df, orig_df,  group_col):
    """
    Calculate the selection parity metric.

    Args:
        _top_df (pandas.DataFrame): DataFrame containing the top-ranked items.
        orig_df (pandas.DataFrame): DataFrame containing the original items.
        group_col (str): Name of the column representing the groups.

    Returns:
        float: Selection parity metric value.
    """
    top_counts = _top_df[group_col].value_counts() / len(_top_df)
    orig_counts = orig_df[group_col].value_counts() / len(orig_df)
    result = top_counts - orig_counts
    res_value = 0
    for gr in orig_df[group_col].unique():
        res_value = abs(res_value - result[gr])
    return np.round(res_value, 2)


def compute_igf_ratio(_top_df, _orig_df, group_col, _orig_sort_col, _id_col):
    """
    Calculate the IGF (Item Group Fairness) ratio.

    Args:
        _top_df (pandas.DataFrame): DataFrame containing the top-ranked items.
        _orig_df (pandas.DataFrame): DataFrame containing the original items.
        group_col (str): Name of the column representing the groups.
        _orig_sort_col (str): Name of the column used for sorting the original items.
        _id_col (str): Name of the column representing the item IDs.

    Returns:
        str: IGF ratio for each group in the format "GROUP: RATIO, GROUP: RATIO, ...".
    """
    # assume _orig_df is sorted according to the _orig_sort_col
    cur_res = dict()
    for group in _orig_df[group_col].unique():
        group_orig = _orig_df[_orig_df[group_col] == group]
        group_top = _top_df[_top_df[group_col] == group]

        top_k_IDS = group_top[_id_col]

        if len(group_orig[~group_orig[_id_col].isin(top_k_IDS)]) == 0:
            igf = 1
        else:
            igf = min(group_orig[group_orig[_id_col].isin(top_k_IDS)][_orig_sort_col]) / max(
                group_orig[~group_orig[_id_col].isin(top_k_IDS)][_orig_sort_col])

        if igf > 1:
            cur_res[group] = 1
        else:
            cur_res[group] = igf

    str_res = ""
    for group in sorted(_orig_df[group_col].unique()):
        str_res = str_res + group.upper() + ":" + str(np.round(cur_res[group], 2)) + ", "

    str_res = str_res.strip(", ")
    return str_res
