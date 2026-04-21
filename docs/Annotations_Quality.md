# Annotations Quality
## Inter-annotator agreement

Anno Rank offers the possibility of computing inter-annotator agreement on the exported annotations. So far, Anno Rank supports computing three IAA's modes (Krippendorf’s Alpha [7], Cohen’s Kappa [5], Weighted Cohen’s Kappa [6]), using the Python agreement library2. This feature can be activated through a configuration file, for example:
         "iaa": {
              "krippendorfs": true,
              "cohens": true,
              "weighted_cohens": true,
              "filter_per_task": true }
, where one has to set the desired IAA metric configuration ("krippendorfs", "cohens", "weighted_cohens") to 'true' for computing the metric or 'false' for not computing the metric. <br>

Enabling "filter_per_task" configuration will group the annotations based on their experiment_id, task_id, and doc_id. If set to false, it will compute the user agreements for every annotating task in the database for a particular dataset. <br>

To compute the IAA metrics for the “shortlisting” feedback collected with the Interaction Annotation UI, the IAA metrics configuration must be included in the config_shortlist_<dataset_name>.json. To compute the IAA metrics for the “label” feedback collected with the Score Annotation UI, the IAA metrics configuration should be included in the config_annotate_score_<dataset_name>.json. <br>

To generate these metrics, the user can execute this command at any time: docker exec annorank-container conda run -n tool_ui python /app/src/evaluate/iaa_metrics.py --dataset <dataset_name>, as long as the MongoDB container is still up. The <dataset_name> should be the same as to the config["data_reader_class"]["name"] in the same configuration file. After executing the docker exec command above, the output of the IAA calculation will be stored in the /output/iaa_metrics.jsonl.<br>

***Example when*** "filter_per_task" ***is True***:
```
{
}, {
    "annotate": {
        "filters": {
            "task_id": "0",
            "exp_id": "2",
            "doc_id": "6655e6b4e5a0a19c08e948c0"
        },
        "iaa_metrics": {
            "krippendorffs": 0.6,
            "cohens": 0.6,
            "weighted_cohens": 0.6
},
        "error_message": "No error"
    }
    "ranking": {
        "filters": {
            "task_id": "0",
            "exp_id": "1",
            "doc_id": "6655e6b4e5a0a19c08e948bf"
        },
        "iaa_metrics": {
            "krippendorffs": 0.5,
            "cohens": 0.5,
            "weighted_cohens": 0.5
},
        "error_message": "No error"
    }
}

```

***Example when*** "filter_per_task" ***is False***:

```
{
        "ranking": {
            "filters": {
                "no_filter": true
            },
            "iaa_metrics": {
                "krippendorffs": 1.0,
                "cohens": 1.0,
                "weighted_cohens": 1.0
},
            "error_message": "No error"
        }
}
```

The value ranges from 0 to 1, where 0 is perfect disagreement about a specific pair query and document and its annotation score, where 1 is ideal agreement for more than one annotator.

## Attention Check

Anno Rank offers the possibility to define an attention check task. In the database the user will have a flag indicating whether the user passed the attention check or not. Using the attention check one could discard the users that did not pass it.
<br>
Example of attention check defined for the Flickr dataset:
```
Interaction Annotate UI:
      "attention_check": {
         "task": {
           "query_title": "1000344755.jpg",
           "ranking_type": "original"
         },
         "correct_answer": [16, 17, 18]
       }
Score Annotate UI:
      "attention_check": {
       "task": {
         "query_title": "1000344755.jpg",
         "index": "2",
         "ranking_type": "original"
},
       "correct_answer": "Relevant"
      }
```

The “correct_answer” indicates the list of documents that the user should shortlist in order to pass the attention check. If the collected feedback from the user differs from the one indicated under “correct_answer” the user will have the attention check failed in the database.
