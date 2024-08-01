import os
import pandas as pd
from data_readers.data_reader import DataReader


class DataReaderAmazon(DataReader):
    def __init__(self, configs):
        super().__init__(configs)

    def transform_data(self):
        """Transform data into pandas.DataFrame and apply cleaning steps.

        Reads the 'amazon.csv' file from the specified data path, drops rows with missing values,
        and performs data transformations on the columns. Returns the transformed data.

        Returns:
            dataframe_query (pandas.DataFrame): A DataFrame containing the transformed query data.
            data_train (pandas.DataFrame): A DataFrame containing the transformed training data.
            data_test (pandas.DataFrame): A DataFrame containing the transformed testing data.
        """
        amazon_product_df = pd.read_csv(os.path.join(self.data_path, 'data', 'amazon.csv'))
        amazon_product_df = amazon_product_df.dropna(how='any', axis=0)

        # the query dataframe
        query_df = pd.DataFrame(columns=['title', 'text'])
        query_df['title'] = amazon_product_df["amazon_category_and_sub_category"]
        query_df['text'] = amazon_product_df["amazon_category_and_sub_category"].apply(lambda x: x.split(">")[-1])

        amazon_product_df["number_of_reviews_display"] = amazon_product_df["number_of_reviews"].apply(lambda x: str(x) + "reviews")

        # split data into train and test
        data_train = amazon_product_df.head(101)
        data_test = amazon_product_df.tail(410)

        dataframe_query = query_df

        return dataframe_query, data_train, data_test
