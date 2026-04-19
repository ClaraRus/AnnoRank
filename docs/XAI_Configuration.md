# XAI Configuration (v1)

XAnnoRank (v1) adds Explainable AI (XAI) support on top of the base configuration. The fields below extend the standard [Configuration File](Configuration_File.md).

## Experiment-level XAI fields

Inside each task entry in the experiment JSON file, set the following field to enable XAI explanations for that task:

- `"show_xai"` — Controls whether an AI explanation is shown to the annotator for this task. Accepted values:
  - `false` — No explanation is shown (same behaviour as v0).
  - `"text"` — Show a textual explanation.
  - `"image"` — Show an image-based explanation (e.g. saliency map, feature-importance bar chart).
  - `"image_text"` — Show both an image and a text explanation side by side.
  - `"factual"` — Show a factual explanation, i.e. reasons *why* the AI reached its decision.
  - `"counterfactual"` — Show a counterfactual explanation, i.e. what would need to change in the candidate profile for the decision to differ.

- `"ranking_type"` — Tag used to look up the correct XAI entry inside the document's `text_xai` / `image_xai` arrays. Each XAI entry stored in the database must carry a matching `"ranking_type"` value so that the correct explanation is retrieved per condition.

## `ui_display_config` XAI fields

- `"task_description_xai"` — Alternative task description shown to annotators when `show_xai` is not `false`. Should explain to the participant that an AI explanation will be provided and ask them to critically evaluate it. When `show_xai` is `false` the standard `"task_description"` is used instead.

- `"instructions_timer"` — (Optional) Minimum number of seconds the annotator must remain on the instructions page before being allowed to continue. Works for both the standard and XAI task descriptions.

## Example XAI config snippet

```json
{
  "data_reader_class": {
    "name": "findhr",
    "score": "Candidate ID",
    "group": "Gender",
    "query": "query",
    "docID": "Candidate ID"
  },
  "ui_display_config": {
    "highlight_match": false,
    "instructions_timer": 5,
    "display_fields": ["Candidate ID", "Education EQF", "Gender_display",
                       "Years of Experience", "Job and Language Skills_display"],
    "task_description": "<b>Read the instructions carefully.</b><br>Your objective …",
    "task_description_xai": "<b>Read the instructions carefully.</b><br>You will also see an AI explanation …",
    "exit_survey": { "title": "Exit Survey", "questions": [] },
    "view_button": true,
    "view_fields": [],
    "shortlist_button": false,
    "shortlist_select": [0, 0]
  },
  "attention_check": { "limit": 2, "reload_tasks": ["1"] },
  "iaa": {
    "krippendorfs": true,
    "cohens": true,
    "weighted_cohens": true,
    "filter_per_task": true
  }
}
```

In the corresponding experiment file each task entry can carry:

```json
{
  "query_title": "Software Engineer",
  "show_xai": "factual",
  "ranking_type": "ranker_LambdaMART"
}
```

See the full working example configs under `configs/findhr_tutorial/`:
- `config_shortlist_findhr_XAI_candidate.json`
- `config_shortlist_findhr_XAI_recruiter.json`
