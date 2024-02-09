
# AnnoRank
We present AnnoRank, a web-based user interface (UI) framework designed to facilitate the collection of both explicit and implicit annotations in the context of information retrieval (IR). 
The tool has three primary functionalities.
First, the tool collects explicit and implicit annotations given a query and a ranked list of items. 
Second, it facilitates explicit annotation of items based on relevance labels in response to a given query. 
Third, the functionality in AnnoRank for comparing rankings serves the purpose of visualizing and assessing a ranked list produced by various fairness interventions or ranking models alongside utility and fairness metrics. 
Given the extensive use of ranking systems, the application supports the presentation of text and images. 
AnnoRank offers support for applying fairness interventions in the pipeline of a ranking system to avoid the propagation of bias in a ranking being returned. 
In addition, the tool is integrated with the Ranklib library, offering a vast range of ranking models that can be applied to the data and displayed in the UI. 
AnnoRank is designed to be flexible, configurable, and easy to deploy to meet diverse requirements and a larger audience. 

# Requirements 
Depending on your development system, instructions on how to install the Docker and MongoDB can be found here:
- Install Docker by following the steps presented here: https://docs.docker.com/engine/install/
- Install Docker Desktop: https://www.docker.com/products/docker-desktop/ 
- Install MongoDB Compass: https://www.mongodb.com/products/tools/compass to view the dataset created and its collections. The connection should be set as mongodb://<IP>:27017. <IP> should be set to IP address for of the machine where the docker 

### Windows:
If you are using Windows make sure you have WSL2. Allow WSL2 usage in docker settings.

# External Resource
In the folder external resources the following can be found:
- AnnoRank.zip - a downloadable version of the tool
- Usability_Study_Anno_Rank.pdf - the usability study conducted for Anno Rank
- Anno_Rank_Documentation.pdf - the documentation provided for Anno Rank

# Export Data
```bash
docker exec -it $(docker ps -q | sed -n '1p') bash -c 'mongoexport --host="localhost:27017" --collection=<collection_name> --db=<db_name> --out=./app/database.json' && docker cp "$(docker ps -q | head -n 1)":./app/database.json <local_path_to_save>
```

# Example: Amazon dataset

Run the following script and type "amazon":
> cd AnnoRank
> 
> ./run_apps.sh 

Before accessing the links you need to wait for the app to finish the install and start. 

To access the Interaction Annotation UI go to the following link: http://localhost:5000/start_ranking/3

To access the Ranking Comparison Visualise UI go to the following link: http://localhost:5001/start_compare/2

To access the Ranking Comparison Annotate UI go to the following link: http://localhost:5002/start_compare_annotate/2

To access the Score Annotate UI go to the following link: http://localhost:5003/start_annotate/1

# Example: Flickr dataset

Run the following script and type "flickr":
> cd AnnoRank
> 
> ./run_apps.sh 

Before accessing the links you need to wait for the app to finish the install and start. 

To access the Interaction Annotation UI go to the following link: http://localhost:5000/start_ranking/2

To access the Ranking Comparison Visualise UI go to the following link: http://localhost:5001/start_compare/3

To access the Ranking Comparison Annotate UI go to the following link: http://localhost:5002/start_compare_annotate/3

To access the Score Annotate UI go to the following link: http://localhost:5003/start_annotate/1 

# Example: Recruitment use-case

Run the following script and type "cvs":
> cd AnnoRank
> 
> ./run_apps.sh

Before accessing the links you need to wait for the app to finish the install and start. 

To access the Interaction Annotation UI go to the following link: http://localhost:5000/start_ranking/1

To access the Ranking Comparison Visualise UI go to the following link: http://localhost:5001/start_compare/3

To access the Ranking Comparison Annotate UI go to the following link: http://localhost:5002/start_compare_annotate/3 

To access the Score Annotate UI go to the following link: http://localhost:5003/start_annotate/2
In order to use the Score Annotate UI with multi dimension annotation adapted for the recruitment use-case, change in "/templates/index_annotate_documents" the line "{% include 'doc_annotate_profile_template.html' %}" with the following: {% include 'doc_annotate_profile_template_recruitment.html' %}


# Tutorial: Example on the XING dataset
1. Download the XING dataset from: https://github.com/MilkaLichtblau/xing_dataset
2. Create the following folder ./datasets/xing/data and save the dataset there
3. The data reader implemented for this dataset can be found in the following python file ./src/data_readers/data_reader_xing.py.

4. The experiment files can be found at the following locations:
 +  ./datasets/xing/experiments/experiment_shortlist.json → to run the Interaction Annotation UI 
 +  ./datasets/xing/experiments/experiment_compare.json → to run the Ranking Comparison UI
 +  ./datasets/xing/experiments/experiment_annotate_score.json → to run the Score Annotate UI


5. The config files can be found under ./configs/xing_tutorial/ 
+ config_create_db_xing.json → configuration used to add data in the database the data
+ config_shortlist_xing.json → to run the Interaction Annotate UI
+ config_compare_xing.json → to run the Ranking Compare Visualise UI
+ config_compare_annotate_xing.json → to run the Ranking Compare Annotate UI
+ config_annotate_score_xing.json → to run the Annotate Score UI


6. Requirements:

+ Install Docker by following the steps presented here: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04 Select the operating system of the device you want to run the app on and proceed with the steps indicated.  

+ Install Docker Desktop: https://www.docker.com/products/docker-desktop/ 

+ Install MongoDB Compass: https://www.mongodb.com/products/tools/compass to view the dataset created and its collections. The connection should be set as mongodb://<IP>:27017. <IP> should be set to IP address for of the machine where the docker container is running. 
 

7. Run the following script and type xing. 
> cd UI-Tool-main
> 
> ./run_apps.sh

Before accessing the links you need to wait for the app to finish the install and start. This tutorial makes use of the ready to use fairness interventions and Ranklib, meaning that the installation time is higher as it needs to install extra packages for the fairness interventions and for the Ranklib library.

To access the Interaction Annotation UI go to the following link: http://localhost:5000/start_ranking/1

To access the Ranking Comparison Visualise UI go to the following link: http://localhost:5001/start_compare/2

To access the Ranking Comparison Annotate UI go to the following link: http://localhost:5002/start_compare_annotate/2 

To access the Score Annotate UI go to the following link: http://localhost:5003/start_annotate/5 


### References
[1] Ke Yang, Joshua R. Loftus, and Julia Stoyanovich. 2021. Causal intersectionality and fair ranking. In Symposium on Foundations of Responsible Computing (FORC).

[2] Meike Zehlike, Francesco Bonchi, Carlos Castillo, Sara Hajian, Mohamed Megahed, and Ricardo Baeza-Yates. 2017. Fa* ir: A fair top-k ranking algorithm. In Proceedings of the 2017 ACM on Conference on Information and Knowledge Management. ACM, 1569–1578.

[3] Dang, V. "The Lemur Project-Wiki-RankLib." Lemur Project,[Online]. Available: http://sourceforge. net/p/lemur/wiki/RankLib.

[4] Van Gysel, C., & de Rijke, M. (2018, June). Pytrec_eval: An extremely fast python interface to trec_eval. In The 41st International ACM SIGIR Conference on Research & Development in Information Retrieval (pp. 873-876).
