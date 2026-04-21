# XAI UI Functionalities (v1)

XAnnoRank (v1) introduces a new Explainable AI (XAI) ranking annotation flow that extends the standard [UI Functionalities](UI_Functionalities.md) with additional pages and interaction patterns.

## New annotation flow

The XAI app (`app_ranking_XAI.py`) adds the following pages before the main ranking task:

1. **Consent Form** (`/consent/<experiment_id>`) — Presented once per user before the experiment begins. The annotator must accept the consent form to proceed. The form content is defined in the `consent_form_template.html` template.

2. **Instructions Page** (`/instructions/<experiment_id>`) — Displays the task description (either `task_description` or `task_description_xai` from the configuration, depending on the `show_xai` flag). If `instructions_timer` is set in the config, the *Next* button is disabled until the timer expires, ensuring annotators read the instructions.

3. **Ranking + XAI Page** (`/start_ranking_XAI/<experiment_id>/index_ranking/<n_task>/<doc_id>`) — The main annotation page. When `show_xai` is not `false`, an explanation block is injected into the page via `xai_section_template.html`.

4. **Per-task Questionnaire** (`/questionnaire/<experiment_id>/<n_task>`) — An optional questionnaire shown after each ranking task, separate from the exit survey.

## XAI explanation modes

The explanation block rendered in the ranking page depends on the value of `show_xai` set for the current task:

| `show_xai` value | What is shown |
|---|---|
| `false` | No explanation block |
| `"text"` | Textual explanation only |
| `"image"` | Image-based explanation only (e.g. saliency map) |
| `"image_text"` | Image and text explanation side by side |
| `"factual"` | Reasons *why* the AI made its decision |
| `"counterfactual"` | What the candidate would need to change for a different outcome |

## XAI interaction tracking

Three new JavaScript modules extend the existing interaction trackers for XAI tasks:

- **`viewDocInfoXAI.js`** — Tracks expand/collapse events on the document info panel within the XAI view.
- **`viewCountsXAI.js`** — Counts the number of times each document panel is opened during an XAI task.
- **`viewTimeXAI.js`** — Records the time spent viewing each document's expanded info panel in an XAI task.

These are analogous to `viewDocInfo.js`, `viewCounts.js`, and `viewTime.js` in v0, and store their data in the same database collections using the same schema.

## New templates

| Template | Purpose |
|---|---|
| `consent_form_template.html` | Consent gate shown before the experiment |
| `task_description_page.html` | Instructions / task briefing page with optional timer |
| `next_button_template.html` | Reusable next-button component used across pages |
| `xai_section_template.html` | Renders the explanation block for any XAI mode |
