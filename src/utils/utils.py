import json
import os
import pathlib
import random
import re


def add_fields_from_data(attr_names, values, object):
    """
    Adds fields to an object from a list of attribute names and corresponding values.

    Args:
        attr_names (list): A list of attribute names.
        values (list): A list of corresponding values for the attributes.
        object (object): The object to which the fields will be added.

    Returns:
        object: The object with the added fields.
    """
    for index, attr_name in enumerate(attr_names):
        object.__setattr__(attr_name, values[index])

    return object

def read_json(file):
    """
    Reads a JSON file and returns its contents as a Python dictionary.

    Args:
        file (str): The path to the JSON file.

    Returns:
        dict: The contents of the JSON file as a Python dictionary.
    """
    with open(file) as f:
        data = json.load(f)
    return data


def clean_text(text, upper=False):
    """
    Cleans the given text by removing special characters and punctuation.

    Args:
        text (str): The text to be cleaned.
        upper (bool, optional): Whether to convert the cleaned text to title case. Defaults to False.

    Returns:
        str: The cleaned text.
    """
    text = re.sub(r'[^a-zA-Z0-9\n]', ' ', text)
    if upper:
        return text.title()
    else:
        return text


def get_ltr_cols(features_cols, score_col, apply_fair_intervention=False):
    """Get columns to be used by the LTR model.

    Args:
        features_cols (list): List of feature columns
        score_col (str): Score column
        apply_fair_intervention (bool): True to train on data changed by the fairness intervention;
         False to train on original data

    Returns:
        list: List of columns to be used by the LTR model.
    """
    original_features = features_cols + [score_col]
    fair_features_cols = [col + '_fair' for col in features_cols]

    if not apply_fair_intervention:
        ltr_cols = original_features
    else:
        ltr_cols = fair_features_cols + [score_col + '_fair']

    return ltr_cols


def check_nan(df, cols_train):
    """
    Check if there are any NaN values in the specified columns of a DataFrame.

    Parameters:
    - df (pandas.DataFrame): The DataFrame to check for NaN values.
    - cols_train (list): A list of column names to check for NaN values.

    Returns:
    - bool: True if there are NaN values in any of the specified columns, False otherwise.
    """
    for col in cols_train:
        if df[col].isnull().values.any():
            return True
    return False


def writeToTXT(file_name_with_path, _df):
    """
    Write a pandas DataFrame to a text file.

    Args:
        file_name_with_path (str): The path and name of the output file.
        _df (pandas.DataFrame): The DataFrame to be written.

    Returns:
        None
    """
    # try:
    #     _df.to_csv(file_name_with_path, header=False, index=False, sep=' ')
    # except FileNotFoundError:
    directory = os.path.dirname(file_name_with_path)
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    print("Make folder ", directory)
    _df.to_csv(file_name_with_path, header=False, index=False, sep=' ')


def writeToCSV(file_name_with_path, _df):
    """
    Write a pandas DataFrame to a CSV file.

    Args:
        file_name_with_path (str): The path and name of the output CSV file.
        _df (pandas.DataFrame): The DataFrame to be written to the CSV file.

    Raises:
        FileNotFoundError: If the specified directory does not exist.

    """
    try:
        _df.to_csv(file_name_with_path, index=False)
    except FileNotFoundError:
        directory = os.path.dirname(file_name_with_path)
        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
        print("Make folder ", directory)
        _df.to_csv(file_name_with_path, index=False)
