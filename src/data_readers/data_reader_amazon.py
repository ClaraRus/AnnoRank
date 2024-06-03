import os
import pandas as pd
from src.data_readers.data_reader import DataReader
class DataReaderAmazon(DataReader):
    def __init__(self, configs):
        super().__init__(configs)

    def transform_data(self):
        amazon_product_df = pd.read_csv(os.path.join(self.data_path, 'data', 'amazon.csv'))
        amazon_product_df = amazon_product_df.dropna(how='any', axis=0)

        query_df = pd.DataFrame(columns=['title', 'text'])
        query_df['title'] = amazon_product_df['amazon_category_and_sub_category']
        query_df['text'] = amazon_product_df['amazon_category_and_sub_category'].split(">")[-1]

        amazon_product_df["number_of_reviews_display"] = amazon_product_df["number_of_reviews"].apply(lambda x: str(x) + "reviews")
        data_train = amazon_product_df.head(101)
        data_test = amazon_product_df.tail(410)

        dataframe_query = query_df
        
        return dataframe_query, data_train, data_test
        
        
