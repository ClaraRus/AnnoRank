import os
import pandas as pd
from pathlib import Path
from data_readers.data_reader import DataReader
project_dir = Path.cwd()
class DataReaderFlickr(DataReader):

    def __init__(self, configs):
        super().__init__(configs)

    def transform_data(self):
        """
        Transform data into pandas.DataFrame and apply cleaning steps.

        Reads the flickr data from a CSV file, performs data preprocessing, and returns the transformed data.

        Returns:
            tuple: A tuple containing the transformed data.
                - dataframe_query (pandas.DataFrame): A DataFrame containing the transformed query data.
                - data_train (pandas.DataFrame): A DataFrame containing the transformed training data.
                - data_test (pandas.DataFrame): A DataFrame containing the transformed testing data.
        """
        flickr_df = pd.read_csv(os.path.join(self.data_path, 'data', 'flickr.csv'))
        flickr_df = flickr_df.dropna(how='any', axis=0)

        # the query dataframe
        query_df = pd.DataFrame(columns=['title', 'text'])
        query_df['title'] = flickr_df['image']
        query_df['text'] = flickr_df['base64']

        # split data into train and test
        data_train = flickr_df.head(10)
        data_test = flickr_df.tail(20)

        dataframe_query = query_df

        return dataframe_query, data_train, data_test
