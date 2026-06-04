
# XAnnoRank
We present XAnnorank, an extension of AnnoRank that supports explainability studies in rankings via user-centered evaluation. XAnnorank provides an easily adaptable user interface (UI) that enables systematic assessment of explainability methods by presenting ranked lists with and without explanations, while collecting both implicit and explicit user feedback. Its flexibility facilitates diverse user design, including different explanation types, datasets, ranking models, and researcher-defined configurations. This updated version supports as well the previous functionalities of AnnoRank: collect interactions between the user and the ranked list of items, collect graded relevance for an item given the displayed query, and compare two rankings and assess which ranking is more suitable given the query and the assessment's requirements. Moreover, AnnoRank offers the researcher the possibility to view the annotations collected and compare two rankings as well as viewing the corresponding evaluation metrics.
  
# Requirements 
Depending on your development system, instructions on how to install the Docker and MongoDB can be found here:
- Install Docker by following the steps presented here: https://docs.docker.com/engine/install/
- Install Docker Desktop: https://www.docker.com/products/docker-desktop/ 
- Install MongoDB Compass: https://www.mongodb.com/products/tools/compass to view the dataset created and its collections. The connection should be set as mongodb://<IP>:27017. <IP> should be set to IP address for of the machine where the docker 
  
## Important remarks:
- Make sure to have the .env file in your cloned repo.
- If you are using Windows make sure you have WSL2. Allow WSL2 usage in docker settings.
-  If the script cannot be executed, this may be caused by Windows line endings. This issue can be resolved by converting the files to Unix format using:
> dos2unix run_apps.sh 
> 
> dos2unix apps_docker.sh
- Please note that whenever the dataset is modified, the `format_data` folder within the dataset directory should be removed before rerunning the script. 

# Export Data
```bash
docker exec -it $(docker ps -q | sed -n '1p') bash -c 'mongoexport --host="localhost:27017" --collection=<collection_name> --db=<db_name> --out=./app/database.json' && docker cp "$(docker ps -q | head -n 1)":./app/database.json <local_path_to_save>
```

# Demo: Recruitment Use Case
This demo supports two user perspectives in a recruitment setting:
1. That of a candidate, where the user impersonates a job seeker who was not selected by the AI system and is asked to critically evaluate the AI's decision based on their profile and the job requirements. 
2. That of a recruiter, where the user acts as a recruiter reviewing the AI-ranked candidate list and must shortlist a defined number of candidates. 

Run the following script and type "findhr":
> cd Annorank
> 
> ./run_apps.sh

To access the tool for the Demo:
- Candidate side: http://localhost:5005/start_ranking_XAI/<exp_id>
  - Exp_id:
    - 101: This experiment is composed only of questionnaires. In our recruitment demonstration we show to a candidate various explanations and ask the candidate to evaluate their usefulness. XAnnoRank supports both the display of text and images in the questionnaires.
    - 102: In this experiment we ask the user to impersonate a job seeker. The user is then presented with the various job descriptions and their profile. The user is asked to interact with the UI presenting in each task a different type of explanation. In the follow-up questionnaire the user is asked to evaluate the previously seen explanation type. In this way XAnnoRank can be used to compare various types of explanation methods.
    - 103: In this experiment we ask the user to impersonate a job seeker. The user is then presented with the various job descriptions and their profile. The user is asked to interact with the UI which this time does not show any explanation. In the follow-up questionnaire the user is asked to evaluate whether the reason for rejection is clear. With such a set-up XAnnoRank can be used to conduct A-B test experiments, where one pool of users is presented with the explanations, and the other without explanations. 
    - 104: In this experiment the user is first presented with the job description and their profile without explanations, in the second part of the study they are presented with the explanation. Each task is followed by a questionnaire evaluating the previously seen explanations and interaction with the UI. In this way one can evaluate the impact of various explanation methods on the user's perception and behaviour. 
- Recruiter side[^1]: http://localhost:5004/start_ranking_XAI/<exp_id>
  - Exp_id:
    - 1: This experiment is composed only of questionnaires. The recruiter is presented with various explanations and asked to evaluate them.
    - 2: This experiment shows various types of explanations followed by a questionnaire. The recruiter is asked to choose the best candidates to be shortlisted.
    - 3: The recruiter is asked to choose the best candidate/s, but without the extra information provided by the explanations. This gives the opportunity to run an A-B test study by showing to a pool of candidates the task without XAI, and to another pool the task with XAI. This is useful in understanding how explanations impact the recruitment process and the recruiter’s behaviour.
    - 4: In this experiment the recruiter is first presented with the recruitment task without the XAI, and in the second part with the XAI.

# External Resource
In the folder external resources, a detailed documentation of XAnnorank can be found [here](https://github.com/ClaraRus/AnnoRank/blob/XAnnoRank/external-resources/XAnno_Rank_Documentation.pdf) to configure it to your own dataset.

[^1] Recruiter Side - experiments are similar to the candidate side, with the difference that they should be shown to a recruiter, and the recruiter is presented with the job description together with the list of candidates who applied to that particular job offer.

