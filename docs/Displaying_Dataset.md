# Displaying a new Dataset

To use the UI with a new dataset, the following steps should be followed:
- Under ```./datasets```, create a new folder called ```<data_name>/data``` and save the
dataset there. Next, under ./datasets create a folder called experiments in which you can define the query-documents pairs to be displayed when running the UI. More details can be found in the following section: Experiment File.
- Under ```./src/data_readers``` create a python file ```data_reader_<data_name>.py```. Inside create a class ```DataReader<Data_name>```. Source code documentation for DataReader class can be found here [Data Readers](Data_Readers.md).
- The ```DataReader<Data_name>``` should implement the transform_data method that should return the following:
    - dataframe_queries : dataframe describing the queries. It should have the following mandatory columns:
        - ```title``` : this is the title of the query
        - ```text``` : this will be displayed in the UI. For example, if the query is a job description, the ‘title’ will be the job title and the ‘text’ will be the job description, which includes the job title. If the query is represented by a word/s set both ‘title’ and ‘text’ to the same value.
    - data_test : dataframe describing the documents to be displayed.
    - data_train : dataframe describing the documents to be used when training a ranker or a fairness intervention.
- Under ./configs create json files following the naming conventions:
  - ```config_shortlist_<data_name>.json``` to run the Interaction Annotate UI
  - ```config_compare_<data_name>.json``` to run the Ranking Compare Visualise UI
  - ```config_compare_annotate_<data_name>.json``` to run the Ranking Compare Annotate UI
    in which one should define the configuration to run the tool with. More details about the configuration file can be found in the following section: Configuration File.



  
