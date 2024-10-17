# Additional Support
## Ranklib Rankers
***Ready to Use*** <br>
The tool offers support for using any model implemented using the ranklib library[3]. It is to be considered that the ranklib library requires java to be installed in the docker container, thus, on the first run it might take longer for the app to start as it first needs to install java. It can be used by defining in the config file the following:
```
"train_ranker_config": {
"name": "Ranklib",
"model_path": "./dataset/<data_name>/models/Ranklib", // path to
save/load the model
 "settings": [{
     "features": ["feature_1", "feature_2", "feature_3"], // list of
features to be considered during training
     "pos_th": 0, // threshold to consider relevant documents
     "rel_max": 500, // maximum relevance that is assigned based on
the ‘score’ column
     "ranker": "RankNet", // ranker name
     "ranker_id": 1, // ranker id
     "metric": "NDCG", // metric to evaluate
     "top_k": 10, // evaluate at top-k
     "lr": 0.000001, // learning rate
     "epochs": 20, //number of epochs
     "train_data":["original"] // define the train data,
     "test_data": ["original"] //define the test data,
     "ranking_type": "ranker_1" }]}
```
For more information on how to use ranklib rankers check the ranklib documentation: https://sourceforge.net/p/lemur/wiki/RankLib%20How%20to%20use//.
<br>

The "train_data" and "test_data" can be set to the following values:
- "original"-thegroundtruthissettobetheoriginalscore
- <ranking_type>-if the ground truth is set to be the score computed using a fairness intervention. 
<br>

The train method saves the input files in the format expected by the ranklib library under ./dataset/<data_name>/models/Ranklib/<train_data>_<test_data>. The model and predictions are saved under ./dataset/<data_name>/models/Ranklib/<train_data>_<test_data>/ranklib_experimen ts/<ranker_name>. <br>

The output of the predict method returns a new dataframe that is in the same format as the original one with an appended column representing the predicted score. The column with the predicted relevance should follow the convention <train_column>__<test_column>. For example if the train and test data is set to be “original”, the predicted score column should be ”score”__”score”, where “score” is the value defined in the config file under the “score” field. If the train and test data are pre-processed by a fairness intervention the predicted score column should be “score“_fair__“score“_fair.
<br>
The new ranking based on the predicted score is saved in the MonogDB database in the collection dataset, in the field rankings. Given the config presented above, the ranking type of saved in the database will be set to ranker_1:“score“__“score“. If a preprocessing fairness intervention is applied on the train/test data, the ranking type saved in the database will be set to ranker_1:preprocessing_1:“score“_fair__“score_fair“

<br>

***Add a new Rankers***

In order to add a new ranker the following steps should be followed:
- Under ./src/rankers create the following python file: ranker_<ranker_name>.py. Inside the python file create the class that implementes the ranker method:
```
class <ranker_name>Ranker(Ranker):
                def __init__(self, configs, data_configs,
                model_path):
                           super().__init__(configs,data_configs,
                      model_path)

```
  - model_path - path to save/load the model
  - configs - dictionary of hyperparameters needed to run the ranker. This is defined in the config file as “settings”.
  - data_configs - dictionary of configs defined for the 
  - data_reader_class. This is needed to be able to access the required columns by the fairness intervention.
- Implement the methods defined in the parent class Ranker, which can be found in ./src/fairness_interventions/ranker.py.
  ```
  def train_model(self, data_train, data_test, experiment)
    data_train - data to train the model
    data_test - data to evaluate the model during training experiment - tuple containing the <train_ranking_type> and <test_ranking_type> defined in the configuration file.
    The train method should save the trained model at the following path:
    self.model_path/<train_ranking_type>__<test_ranking_ type>.
  def predict(self, data, experiment)
    data - data to run the model on and generate the predicted ranking experiment - tuple containing the <train_ranking_type> and <test_ranking_type> defined in the configuration file.
    The predict method should load the model from self.model_path/<train_ranking_type>__<test_ranking_ type> and apply it on the data.
    The method should return a new dataframe that is in the same format as data with an appended column representing the predicted score. The column with the predicted score should follow the convention <train_score_column>__<test_score_column>.
    For example if the <train_ranking_type> and <test_ranking_type> is set to be “original”, the predicted score column should be ”score”__”score”. If the train and test data are pre-processed by a fairness intervention the predicted score column should be ”score”_fair__”score”_fair, where “score” is the value defined in the config file under the “score” field.
  ```
- If needed any files related to the fairness method can be saved under ./src/rankers/modules/<ranker_name>
- Define the new ranker in ./src/constants in the dictionary containing the rankers.
- Using the new ranker:
```
"train_ranker_config": {
"name": "<ranker_name>" // same as the key defined in the
   dictionary,
        "model_path":
   "./dataset/<data_name>/models/<ranker_name>", // path to
   save/load the model
"settings": [{
// define any configs needed to run the ranker "features": ["feature_1", "feature_2", "feature_3"],
   // list of features to be considered during training
"train_data":["original"], // define the train data
                "test_data": ["original"], //define the test data
                "ranking_type": "ranker_1"
                }]}

```

## Fairness Intervention

***Ready to Use*** <br>
The tool supports applying:
- post-processing fairness intervention: FA*IR[2]. It can be used by defining in the config file the following:
```
"post_processing_config": {
       "name": "FA*IR",
       “model_path”: “”, //empty as there is no model to save
       "settings": [{
            "k": 10,
            "p": 0.7,
            "alpha": 0.1
            "ranking_type": "postprocessing_1"}]
}

```

- pre-processing fairness intervention: CIF-Rank. It can be used by defining in the config file the following:
```
 "pre_processing_config": {
            "name": "CIFRank",
            "model_path": "./dataset/<data_name>/models/CIFRank", // path
      to save/load the model
            "settings": [{
                   "pos_th": 0, //threshold to consider positive documents
                   "control": "group_value", //control group, the group
                  towards which we convert all the data in a counterfactual
                  world
                   "features": ["field_1", "field_2", "field_3"]//list of
            features (columns from the dataframe) to be considered as
            mediators
}] }

```

It is to be considered that the fairness interventions might require additional libraries to be installed in the docker container, thus, on the first run it might take longer for the app to start as it first needs to install the required libraries.

## Add a new fairness method

