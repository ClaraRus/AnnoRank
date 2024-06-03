import argparse
import json
from json.decoder import JSONDecodeError
import os
import sys
sys.path.append('/app/')
# print(sys.path)
import numpy as np
import math
import sys
from config import Config
from mongoengine import *
from agreement.utils.transform import pivot_table_frequency
from agreement.utils.kernels import linear_kernel
from agreement.metrics import cohens_kappa, krippendorffs_alpha
import database
def create_unique_ids_agreement(data):
    """
    data is a list of list data, where it stores values with structure such as: 
    (exp_id, task_id, query, doc), user_id, score, for example:
    [[(1, 2, 'project_manager', 'axasfasdfas'), '9870', 5],
    [(1, 3, 'project_manager', 'axasfasdfas'), '9870', 5]
    and will return output such as:
    [["id_1", '9870', 5],
    ["id_1", 9870, 5]
    """
    unique_ids = {}
    id_counter = 1
    
    for i in range(len(data)):
        key = data[i][0]
        if key not in unique_ids:
            unique_ids[key] = f"id_{id_counter}"  #assign a new unique id
            id_counter += 1
        data[i][0] = unique_ids[key]
    data = np.array(data)
    return data
    
def compute_kappas(data, krippendorffs, cohens, weighted_cohens, filter_attribute, mode):
    """
        filter_attribute is an dictionary where it shows the filter attribute that the config file mentioned
    """
    k_kappa = -1.0
    cohens_k = -1.0
    weighted_cohens_k = -1.0
    if len(data)>=3:
        questions_answers_table = pivot_table_frequency(data[:, 0], data[:, 2])
        users_answers_table = pivot_table_frequency(data[:,1], data[:,2])

        if krippendorffs:
            k_kappa = krippendorffs_alpha(questions_answers_table)

        if cohens:
            cohens_k = cohens_kappa(questions_answers_table, users_answers_table)

        if weighted_cohens:
            weighted_cohens_k = cohens_kappa(questions_answers_table, users_answers_table, weights_kernel=linear_kernel)

    if len(data)==0:
        k_kappa = -1.0
        cohens_k = -1.0
        weighted_cohens_k = -1.0
        message = "No data"
    elif math.isnan(k_kappa) or math.isnan(cohens_k) or math.isnan(weighted_cohens_k):
        if len(data)<3 and len(data) >0:
            message = "There should be at least 3 raters"     
        else:
            message = "nan values for one/all IAA metrics"   
    else:
        message = "No error"
    new_data = {mode: {
                "filters": filter_attribute, #the filter attribute, can be exp_id or task_id or query
                "iaa_metrics":
                    {"krippendorffs": k_kappa, "cohens": cohens_k, "weighted_cohens": weighted_cohens_k},
                "error_message": message}}
                
    write_to_file(new_data, "iaa_metrics.jsonl")
    
def compute_iaa_annotate(krippendorffs, cohens, weighted_cohens):
    # is_per_experiment = configs_annotate["iaa"]["filter"]["per_experiment"]
    is_per_task = configs_annotate["iaa"]["filter_per_task"]

    all_users = database.User.objects()
    users_rates_dataset = []
    exp_unique_id_list = []
    task_unique_id_list = []
    doc_unique_id_list = []
    for user in all_users:
        user_id = user._user_id
        for task_visited in user.tasks_visited:
            temp = []
            interaction_score = task_visited.interaction_score
            exp_id = task_visited.exp
            # task_id = task_visited.task
            #replace the task id with the query
            task_id = task_visited.task
            doc = interaction_score.doc
            #created a list that stores unique exp_id and task_id for further filtering
            if exp_id not in exp_unique_id_list and exp_id !="":
                exp_unique_id_list.append(exp_id)
            if task_id not in task_unique_id_list and task_id !="":
                task_unique_id_list.append(task_id)
            if doc not in doc_unique_id_list:
                doc_unique_id_list.append(doc)
            if interaction_score.score != "":
                temp.append((exp_id, task_id, interaction_score.doc))
                temp.append(user_id)
                if str.isdigit(interaction_score.score):
                    temp.append(int(interaction_score.score))
                else:
                    temp.append(interaction_score.score)
                # print(len(temp))
                users_rates_dataset.append(temp)
            else:
                continue

    # print("annotate exp_unique_id_list", exp_unique_id_list)
    # print("annotate task_unique_id_list", task_unique_id_list)
    # if is_per_experiment: #i dont think this will work
    #     for exp_id in exp_unique_id_list:
    #         grouped_data = [item for item in users_rates_dataset if isinstance(item[0], tuple) and item[0][0] == exp_id]
    #         transformed_data = [[exp_id, user_id, score] for [(exp_id, task_id, doc_id), user_id, score] in grouped_data]
    #         transformed_data = np.array(transformed_data)
    #         print("annotate per experiment", transformed_data)
    #         compute_kappas(transformed_data, krippendorffs, cohens, weighted_cohens, "exp_id", exp_id, "annotate")
    
    if is_per_task: #task_id is a query
        filter_attribute = {}
        for exp_id in exp_unique_id_list:
            for task_id in task_unique_id_list:
                for doc_id in doc_unique_id_list:
                    filter_attribute["task_id"] = task_id
                    filter_attribute["exp_id"] = exp_id
                    filter_attribute["doc_id"] = doc_id
                    grouped_data = [item for item in users_rates_dataset if isinstance(item[0], tuple) and item[0][0] == exp_id and item[0][1] == task_id and item[0][2] == doc_id]
                    #after grouping the doc_id will be the same, so its a good query_id for computing the iaa
                    transformed_data = [[doc_id, user_id, score] for [(exp_id, task_id, doc_id), user_id, score] in grouped_data]
                    transformed_data = np.array(transformed_data)
                    print("annotate per task", transformed_data)
                    compute_kappas(transformed_data, krippendorffs, cohens, weighted_cohens, filter_attribute, "annotate")

    if not is_per_task:
        filter_attribute = {}
        filter_attribute["no_filter"] = True
        users_rates_dataset = create_unique_ids_agreement(users_rates_dataset)
        compute_kappas(users_rates_dataset, krippendorffs, cohens, weighted_cohens, filter_attribute, "annotate")
        
def compute_iaa_ranking(krippendorffs, cohens, weighted_cohens):
    # is_per_experiment = configs_annotate["iaa"]["filter"]["per_experiment"]
    is_per_task = configs_annotate["iaa"]["filter_per_task"]

    all_users = database.User.objects()
    users_rates_dataset = []
    exp_unique_id_list = []
    task_unique_id_list = []
    doc_unique_id_list = []

    for user in all_users:
        user_id = user._user_id
        for task_visited in user.tasks_visited:
            exp_id = task_visited.exp
            #in the shortlist, task is the task_id and not query id
            task_id = task_visited.task
            # i = 0
            if exp_id not in exp_unique_id_list and exp_id !="":
                exp_unique_id_list.append(exp_id)
            if task_id not in task_unique_id_list and task_id !="":
                task_unique_id_list.append(task_id)
                
            for interaction in task_visited.interactions:
                temp = []
                doc_id = interaction.doc_id
                label = interaction.shortlisted
                if doc_id not in doc_unique_id_list:
                    doc_unique_id_list.append(doc_id)
                if label != "":
                    temp.append((exp_id, task_id, doc_id))
                    temp.append(user_id)
                    if str.isdigit(label):
                        temp.append(int(label))
                    else:
                        temp.append(label)
                    users_rates_dataset.append(temp)
                else:
                    continue
                
    # if is_per_experiment:
    #     for exp_id in exp_unique_id_list:
    #         grouped_data = [item for item in users_rates_dataset if isinstance(item[0], tuple) and item[0][0] == exp_id]
    #         transformed_data = [[exp_id, user_id, score] for [(exp_id, task_id), user_id, score] in grouped_data]
    #         transformed_data = np.array(transformed_data)
    #         print("annotate per experiment", transformed_data)
    #         compute_kappas(transformed_data, krippendorffs, cohens, weighted_cohens, "exp_id", exp_id, "ranking")
            
    if is_per_task: 
        """
            when the is_per_task is activated, it will filter based on the exp_id, task_id and doc_id. 
        """
        filter_attribute = {}
        for exp_id in exp_unique_id_list:
            for task_id in task_unique_id_list:
                for doc_id in doc_unique_id_list:
                    filter_attribute["task_id"] = task_id
                    filter_attribute["exp_id"] = exp_id
                    filter_attribute["doc_id"] = doc_id
                    grouped_data = [item for item in users_rates_dataset if isinstance(item[0], tuple) and item[0][0] == exp_id and item[0][1] == task_id and item[0][2] == doc_id]
                    transformed_data = [[doc_id, user_id, score] for [(exp_id, task_id, doc_id), user_id, score] in grouped_data]
                    transformed_data = np.array(transformed_data)
                    # grouped_data = create_unique_ids_agreement(grouped_data)
                    # print("annotate per task", transformed_data)
                    compute_kappas(grouped_data, krippendorffs, cohens, weighted_cohens, filter_attribute, "ranking")
            
            
    if not is_per_task:
        #we dont have any filter in this case, so it will take every possible scoring tasks into account
        #without grouping we have to create incremental unique id for a single tuple
        filter_attribute = {}
        filter_attribute["no_filter"] = True
        users_rates_dataset = create_unique_ids_agreement(users_rates_dataset)
        compute_kappas(users_rates_dataset, krippendorffs, cohens, weighted_cohens, filter_attribute, "ranking")
      
def write_to_file(new_data, filename):
    filename = "./output/"+filename
    list_obj = []
    if not os.path.isfile(filename):
        print("The file does not exist. Creating a new file.")
        with open(filename, 'w') as fp:
            json.dump(list_obj, fp)
    else:
        try:
            with open(filename) as fp:
                list_obj = json.load(fp)
                if not list_obj:
                    print("The JSON file is empty.")
                else:
                    print("The JSON file is not empty.")
        except JSONDecodeError:
            print("The file is empty or not in valid JSON format.")
            
    modified_dict = {key: value.replace("'", '\"') if isinstance(value, str) else value for key, value in new_data.items()}
    list_obj.append(modified_dict)

    with open(filename, 'w') as file:
        # json_line = json.dumps(list_obj)
        json.dump(list_obj, file, indent=4, separators=(',',': '))
     
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset')
    # parser.add_argument('--iaa_metrics')
    args = parser.parse_args()
    f_ranking = f"./configs/{args.dataset}_tutorial/config_shortlist_{args.dataset}.json"
    f_annotate = f"./configs/{args.dataset}_tutorial/config_annotate_score_{args.dataset}.json"
    print(f_ranking)
    print(f_annotate)
    with open(f_ranking) as f:
        configs_shortlist = json.load(f)
    with open(f_annotate) as f:
        configs_annotate = json.load(f)

    connect(configs_shortlist["data_reader_class"]["name"], host=f'mongodb://{"mongo-container"}:{27017}/{configs_shortlist["data_reader_class"]["name"]}', port=27017)
        
    krippendorffs_ranking = configs_shortlist["iaa"]["krippendorfs"]
    cohens_ranking = configs_shortlist["iaa"]["cohens"]
    weighted_cohens_ranking = configs_shortlist["iaa"]["weighted_cohens"]
    krippendorffs_annotate = configs_annotate["iaa"]["krippendorfs"]
    cohens_annotate = configs_annotate["iaa"]["cohens"]
    weighted_cohens_annotate = configs_annotate["iaa"]["weighted_cohens"]
    compute_iaa_annotate(krippendorffs_annotate, cohens_annotate, weighted_cohens_annotate)
    compute_iaa_ranking(krippendorffs_ranking, cohens_ranking, weighted_cohens_ranking)
    
    
    
    
    