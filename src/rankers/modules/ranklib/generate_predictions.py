import os
from utils.utils import get_ltr_cols


def get_prediction_scores(file_path, ranker, file_name='prediction.txt'):
    """
        Retrieves prediction scores from the specified RankLib prediction file.

        Args:
            file_path (str): Path to the directory containing the prediction files.
            ranker (str): Ranker name used to find the prediction file.
            file_name (str): Name of the prediction file. Default is 'prediction.txt'.

        Returns:
            dict: Dictionary where keys are UUIDs and values are their prediction scores.

        Raises:
            ValueError: If no prediction file is found at the specified path.
    """
    # return a dict in which key is the uuid and value is their prediction score
    # score is used to retrieve the relative order, not for other use!!!
    pred_latest_path = file_path + "/ranklib-experiments/" + ranker + "/"
    # retrieve the latest experiment folder
    sub_exp = [x for x in os.listdir(pred_latest_path) if "experiments_" in x]
    exp_suffix = max([os.path.join(pred_latest_path, d) for d in sub_exp], key=os.path.getmtime)[-15:]
    pred_latest_path = pred_latest_path + "experiments_" + exp_suffix  + "/predictions/" + file_name
    if os.path.exists(pred_latest_path):
        print("**** Reading pred at", pred_latest_path)
        with open(pred_latest_path, "r") as text_file:
            ranker_lines = text_file.read().splitlines()

        preds = [(li.split(" ")[2][0:li.split(" ")[2].find(";rel=")].replace("docid=", ""), int(li.split(" ")[3])) for li in
         ranker_lines]
        ranker_pred = dict(preds)
        return ranker_pred
    else:
        print("No prediction found in ", pred_latest_path, "!\n")
        raise ValueError


def get_LTR_predict(count_df, ranklib_path, ranker, experiment, data_configs, features):
    """
        Integrates RankLib predictions into the provided DataFrame.

        Args:
            count_df (DataFrame): DataFrame containing the data to be ranked.
            ranklib_path (str): Path to the RankLib predictions.
            ranker (str): Ranker name used to find the prediction file.
            experiment (tuple): Tuple containing the <train_ranking_type> and <test_ranking_type> defined
            in the configuration file.
            data_configs (dict): Configuration dict of the dataset.
            features (list): List of feature columns.

        Returns:
            DataFrame: DataFrame with RankLib predictions added and sorted by query.
    """
    test_cols = get_ltr_cols(features, data_configs['score'], "original" not in experiment[0])
    train_cols = get_ltr_cols(features, data_configs['score'], "original" not in experiment[1])

    count_df = count_df.sort_values(data_configs['docID'])
    count_df['docID_int'] = count_df[data_configs['docID']].astype('category').cat.codes

    experiment_string =  experiment[0] + "__" + experiment[1]
    ri_pred = get_prediction_scores(os.path.join(ranklib_path, experiment_string), ranker)
    pred_y_col = train_cols[-1] + "__" + test_cols[-1]
    count_df = count_df[count_df["docID_int"].astype(str).isin([x for x in ri_pred])]
    count_df.loc[: ,pred_y_col] = count_df["docID_int"].apply(lambda x: ri_pred[str(x)])
    count_df = count_df.sort_values(data_configs['query'])

    return count_df
