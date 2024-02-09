import os
import pandas as pd
from pathlib import Path
from src.data_readers.data_reader import DataReader
project_dir = Path.cwd()
class DataReaderFlickr(DataReader):

    def __init__(self, configs):
        super().__init__(configs)

    def transform_data(self):
        flickr_df = pd.read_csv(os.path.join(self.data_path, 'data', 'flickr.csv'))
        flickr_df = flickr_df.dropna(how='any', axis=0)

        #the query
        query_df = pd.DataFrame(columns=['title', 'text'])
        query_df['title'] = flickr_df['image']
        query_df['text'] = flickr_df['base64']

        data_train = flickr_df.head(10)
        data_test = flickr_df.tail(20)

        dataframe_query = query_df

        return dataframe_query, data_train, data_test
