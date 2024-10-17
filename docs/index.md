# AnnoRank

AnnoRank is a web-based user interface (UI) framework designed to facilitate the collection of both explicit and implicit annotations in the context of information retrieval (IR). The tool has three primary functionalities. First, the tool collects explicit and implicit annotations given a query and a ranked list of items. Second, it facilitates explicit annotation of items based on relevance labels in response to a given query. Third, the functionality in AnnoRank for comparing rankings serves the purpose of visualizing and assessing a ranked list produced by various fairness interventions or ranking models alongside utility and fairness metrics. Given the extensive use of ranking systems, the application supports the presentation of text and images. AnnoRank offers support for applying fairness interventions in the pipeline of a ranking system to avoid the propagation of bias in a ranking being returned. In addition, the tool is integrated with the Ranklib library, offering a vast range of ranking models that can be applied to the data and displayed in the UI. AnnoRank is designed to be flexible, configurable, and easy to deploy to meet diverse requirements and a larger audience.

## Requirements

Depending on your development system, instructions on how to install the Docker and MongoDB can be found here:

- Install Docker by following the steps in [Docker Installation](https://docs.docker.com/engine/install/)
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Install [MongoDB Compass](https://www.mongodb.com/products/tools/compass) to view the dataset created and its collections. The connection should be set as mongodb://:27017. should be set to IP address for of the machine where the docker



### Windows:
If you are using Windows make sure you have WSL2. Allow WSL2 usage in docker settings.

## Export Data
```bash
docker exec -it $(docker ps -q | sed -n '1p') bash -c 'mongoexport --host="localhost:27017" --collection=<collection_name> --db=<db_name> --out=./app/database.json' && docker cp "$(docker ps -q | head -n 1)":./app/database.json <local_path_to_save>
```

More information about the software usage, UI and database configurations, and others additional support can be found in these pages. 
[UI Functionalities](UI_Functionalities.md)<br>
[Displaying a new Dataset](Displaying_Dataset.md)<br>
[Configuration File](Configuration_File.md)<br>
[Database Pipeline](Database_Pipeline.md)<br>
[Database Structure](Database_Structure.md)<br>



See [the API documentation](my_page.md) [Annotate Document App](Annotate_Document_App.md). Make sure to check out23.
