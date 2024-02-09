import os
import pandas as pd
from src.data_readers.data_reader import DataReader
import json

from src.utils import clean_text


def candidate_to_text(candidate):
    for col in candidate.columns:
        if isinstance(candidate[col][0], list):
            text = ""
            first=True
            if len(candidate[col][0]) > 0:
                if isinstance(candidate[col][0][0], dict):
                    for item in candidate[col][0]:
                        for key in item.keys():
                            text = text + clean_text(key, upper=True) + ': '
                            text = text + clean_text(item[key]) + '\n'
                            if first:
                                candidate[col+"_display"] = text
                                first=False
                            else:
                                candidate[col + "_view"] = text
                        text = text + '\n'
                else:
                    values = candidate[col][0]
                    for val in values:
                        text = text + clean_text(val) + ', '
                    text = text.strip(', ') + '\n'
                    candidate[col+"_display"] = text
        else:
            if col == '_name':
                candidate['name_display'] = candidate[col]
            else:
                candidate[col.replace('_', '') + "_protected"] = candidate[col]

    return candidate


class DataReaderCvs(DataReader):

    def __init__(self, configs):
        super(DataReaderCvs, self).__init__(configs=configs)

    def query_to_text(self, query):
        query_text = ""
        for col in query.columns:
            query_text = query_text + clean_text(col, upper=True) + "\n"
            if isinstance(query[col][0][0], dict):
                values = query[col][0][0]
                for key in values.keys():
                    if values[key] != '':
                        query_text = query_text + clean_text(key, upper=True) + ': '
                        query_text = query_text + clean_text(values[key]) + '\n'
            else:
                values = query[col][0]
                for val in values:
                    query_text = query_text + clean_text(val) + ', '
                query_text = query_text.strip(', ') + '\n'
            query_text = query_text + '\n'
        return query_text

    def transform_data(self):
        occupation_dirs = [dir_name for dir_name in os.listdir(os.path.join(self.data_path, 'data')) if
                           dir_name != 'experiments' and dir_name != 'format_data' and dir_name != 'models']
        dataframes_occupations = []
        dataframes_candidates = []
        for dir_name in occupation_dirs:
            # Read query description and format the query as plain text
            with open(os.path.join(self.data_path, 'data', dir_name, 'description.json'), 'r') as json_file:
                query = json.load(json_file)
            query = pd.json_normalize(query)
            query['text'] = clean_text(dir_name, upper=True) + "\n" + self.query_to_text(query)
            query['title'] = dir_name
            dataframes_occupations.append(query)

            # List all files in the folder with a .json extension
            json_files = [file for file in os.listdir(os.path.join(self.data_path, 'data', dir_name)) if
                          file.endswith('.json') and file != 'description.json']

            # Iterate over each JSON file
            for json_file in json_files:
                file_path = os.path.join(self.data_path, 'data',dir_name, json_file)

                with open(os.path.join(self.data_path, 'data',dir_name, file_path), 'r') as json_file:
                    candidate_data = json.load(json_file)

                candidate_data = pd.json_normalize(candidate_data)
                candidate_data = candidate_to_text(candidate_data)

                candidate_data['query'] = dir_name

                dataframes_candidates.append(candidate_data)

        # Concatenate all DataFrames into a single DataFrame
        data_test = pd.concat(dataframes_candidates, ignore_index=True)
        data_train = data_test

        dataframe_occupations = pd.concat(dataframes_occupations, ignore_index=True)


        return dataframe_occupations, data_train, data_test
