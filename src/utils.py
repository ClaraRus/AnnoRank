import json
import os
import pathlib
import random
import re


def add_fields_from_data(attr_names, values, object):
    for index, attr_name in enumerate(attr_names):
        # setattr(object, attr_name, values[index])
        object.__setattr__(attr_name, values[index])

    return object

def read_json(file):
    with open(file) as f:
        data = json.load(f)
    return data


def clean_text(text, upper=False):
    text = re.sub(r'[^a-zA-Z0-9\n]', ' ', text)
    if upper:
        return text.title()
    else:
        return text


def get_ltr_cols(med_cols, score_col, experiment):
    original_features = med_cols + [score_col]
    fair_features_cols = [col + '_fair' for col in med_cols]

    if experiment == 'original':
        ltr_cols = original_features
    else:
        ltr_cols = fair_features_cols + [score_col + '_fair']

    return ltr_cols


def check_nan(df, cols_train):
    for col in cols_train:
        if df[col].isnull().values.any():
            return True
    return False


def writeToTXT(file_name_with_path, _df):
    # try:
    #     _df.to_csv(file_name_with_path, header=False, index=False, sep=' ')
    # except FileNotFoundError:
    directory = os.path.dirname(file_name_with_path)
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    print("Make folder ", directory)
    _df.to_csv(file_name_with_path, header=False, index=False, sep=' ')


def writeToCSV(file_name_with_path, _df):
    try:
        _df.to_csv(file_name_with_path, index=False)
    except FileNotFoundError:

        directory = os.path.dirname(file_name_with_path)
        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
        print("Make folder ", directory)
        _df.to_csv(file_name_with_path, index=False)
