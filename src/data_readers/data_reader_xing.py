"""
Created on 1.2.2016

@author: mohamed.megahed
"""
import ast
import json
import glob
import datetime
import math
import os
import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from data_readers.data_reader import DataReader

'''
Created on 23.12.2016

@author: meike.zehlike
'''
import uuid


class Candidate(object):
    """
    represents a candidate in a set that is passed to a search algorithm
    a candidate composes of a qualification and a list of protected attributes (strings)
    if the list of protected attributes is empty/null this is a candidate from a non-protected group
    natural ordering established by the qualification
    """

    def __init__(self, work_experience, edu_experience, hits, qualification, protectedAttributes, member_since, degree):
        """
        @param qualification : describes how qualified the candidate is to match the search query
        @param protectedAttributes: list of strings that represent the protected attributes this
                                    candidate has (e.g. gender, race, etc)
                                    if the list is empty/null this is a candidate from a non-protected group
        """
        self.__qualification = qualification
        self.__protectedAttributes = protectedAttributes
        self.__work_experience = work_experience
        self.__edu_experience = edu_experience
        self.__member_since = member_since
        self.__hits = hits
        self.__degree = degree
        # keeps the candidate's initial qualification for evaluation purposes
        self.__originalQualification = qualification
        self.uuid = uuid.uuid4()

    @property
    def qualification(self):
        return self.__qualification

    @qualification.setter
    def qualification(self, value):
        self.__qualification = value

    @property
    def originalQualification(self):
        return self.__originalQualification

    @originalQualification.setter
    def originalQualification(self, value):
        self.__qualification = value

    @property
    def isProtected(self):
        '''
        true if the list of ProtectedAttribute elements actually contains anything
        false otherwise
        '''
        return not self.__protectedAttributes == []


class DataReaderXing(DataReader):
    """
    reads profiles collected from Xing on certain job description queries
    profiles are available in JSON format
    they are read into a data frame indexed by the search queries we used to obtain candidate profiles

    the columns consists of arrays of Candidates, the protected ones, the non-protected ones and
    one that contains all candidates in the same order as was collected from Xing website.

                             |          PROTECTED            |            NON-PROTECTED            |       ORIGINAL ORDERING
    Administrative Assistant | [protected1, protected2, ...] | [nonProtected1, nonProtected2, ...] | [nonProtected1, protected1, ...]
    Auditor                  | [protected3, protected4, ...] | [nonProtected3, nonProtected3, ...] | [protected4, nonProtected3, ...]
            ...              |            ...                |               ...                   |             ...


    the protected attribute of a candidate is their sex
    a candidate's sex was manually determined from the profile name
    depending on the dominating sex of a search query result, the other one was set as the protected
    attribute (e.g. for administrative assistant the protected attribute is male, for auditor it's female)
    """

    EDUCATION_OR_JOB_WITH_NO_DATES = 3  # months count if you had a job that has no associated dates
    EDUCATION_OR_JOB_WITH_SAME_YEAR = 6  # months count if you had a job that started and finished in the same year
    EDUCATION_OR_JOB_WITH_UNDEFINED_DATES = 1  # month given that the person entered the job

    def __init__(self, configs):
        super().__init__(configs)

    def transform_data(self):
        """
        Transform data into pandas.DataFrame and apply cleaning steps.

        Reads the XING data from a JSON file, performs data preprocessing, and returns the transformed data.

        Returns:
            tuple: A tuple containing the transformed data.
                - dataframe_query (pandas.DataFrame): A DataFrame containing the transformed query data.
                - data_train (pandas.DataFrame): A DataFrame containing the transformed training data.
                - data_test (pandas.DataFrame): A DataFrame containing the transformed testing data.
        """

        dataset = self.concat_data()

        dataset[self.query_col] = dataset[self.query_col].apply(lambda x: x.title())
        dataset["edu_experience_string"] = dataset["edu_experience"].apply(lambda x: str(x) + (" months"))
        dataset["work_experience_string"] = dataset["work_experience"].apply(lambda x: str(x) + (" months"))
        dataset["member_since_string"] = dataset["member_since"].apply(lambda x: "Member Since: " + str(x))
        dataset["degree_string"] = dataset["degree"].apply(lambda x: "Degree: " + str(x))

        # the query dataframe
        dataset_queries = pd.DataFrame(columns=['title', 'text'])
        dataset_queries['text'] = dataset[self.query_col].unique()
        dataset_queries['title'] = dataset[self.query_col].unique()

        data_train, data_test = self.create_train_test_split(dataset)
        return dataset_queries, data_train, data_test

    def create_train_test_split(self, dataset):
        data_train_list = []
        data_test_list = []
        for query, group in dataset.groupby([self.query_col]):
            data_train = []
            data_test = []
            for group, gender_group in group.groupby(['gender']):
                if len(gender_group) >= 2:
                    data_train_gr, data_test_gr = train_test_split(gender_group, test_size=0.3)
                    data_train.append(data_train_gr)
                    data_test.append(data_test_gr)
            if len(data_train) == 2:
                data_train_list.append(pd.concat(data_train))
                data_test_list.append(pd.concat(data_test))
        data_train = pd.concat(data_train_list)
        data_test = pd.concat(data_test_list)

        return data_train, data_test

    def concat_data(self):
        entireDataSet = pd.DataFrame(columns=['protected', 'nonProtected', 'originalOrdering'])
        files = glob.glob(os.path.join(self.data_path, 'data', '*.json'))

        df_lists = []
        for filename in files:
            key, protected, nonProtected, origOrder = self.__readFileOfQuery(filename)
            entireDataSet.loc[key] = [protected, nonProtected, origOrder]
            df_temp = pd.DataFrame([o.__dict__ for o in origOrder])
            df_temp['title'] = key
            df_lists.append(df_temp)
        dataset = pd.concat(df_lists)
        new_cols = []
        for col in dataset.columns:
            new_col = col.split('__')[-1]
            if new_col == 'uuid':
                new_col = 'cid'
            if new_col == 'protectedAttributes':
                new_col = self.sensitive_col
            new_cols.append(new_col)
            dataset[new_col] = dataset[col].values
        dataset = dataset[new_cols]
        return dataset

    def dumpDataSet(self, pathToFile):
        with open(pathToFile, 'wb') as handle:
            pickle.dump(self.entireDataSet, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def __readFileOfQuery(self, filename):
        """
        takes one .json file and reads all information, creates candidate objects from these
        information and sorts them into 3 arrays. One contains all protected candidates, one contains
        all non-protected candidates, one contains all candidates in the same order as they appear
        in the json-file

        @param filename: the json's filename

        @return:
            key: the search query string
            protected: array that contains all protected candidates
            nonProtected: array that contains all nonProtected candidates

        """
        protected = []
        nonProtected = []
        originalOrdering = []

        currentfile = open(filename)
        data = json.load(currentfile)

        xingSearchQuery = data['category']
        # if the Xing search query results in a gender neutral list,
        # we take female as the protected attribute
        protectedAttribute = 'm' if data['dominantSexXing'] == 'f' else 'f'

        for r in data['profiles']:
            # determine Member since / Hits
            if 'memberSince_Hits' in r['profile'][0]:
                hits_string = r['profile'][0]['memberSince_Hits']
                hits = hits_string.split(' / ')[1]
                member_since = hits_string.split(' / ')[0]
            else:
                hits = 1
                member_since = "unknown"

            work_experience = self.__determineWorkMonths(r)
            edu_experience = self.__determineEduMonths(r)
            if "education" in r['profile'][0]:
                degree = r['profile'][0]['education']['degree']
            else:
                degree = "unknown"
            score = (work_experience + edu_experience) * int(hits)

            if self.__determineIfProtected(r, protectedAttribute):
                protected.append(
                    Candidate(work_experience, edu_experience, hits, score, [protectedAttribute], member_since, degree))
            else:
                nonProtected.append(Candidate(work_experience, edu_experience, hits, score, [], member_since, degree))

            sex = r['profile'][0]['sex']
            originalOrdering.append(Candidate(work_experience, edu_experience, hits, score, sex, member_since, degree))

        protected.sort(key=lambda candidate: candidate.qualification, reverse=True)
        nonProtected.sort(key=lambda candidate: candidate.qualification, reverse=True)

        self.__normalizeQualifications(protected + nonProtected)
        self.__normalizeQualifications(originalOrdering)

        currentfile.close()
        return xingSearchQuery, protected, nonProtected, originalOrdering

    def __normalizeQualifications(self, ranking):
        # find highest qualification of candidate
        qualifications = [ranking[i].qualification for i in range(len(ranking))]
        highest = max(qualifications)
        for candidate in ranking:
            candidate.qualification = candidate.qualification / highest
            candidate.originalQualification = candidate.originalQualification / highest

    def __determineIfProtected(self, r, protAttr):
        """
        takes a JSON profile and finds if the person belongs to the protected group

        Parameter:
        ---------
        r : JSON node
        a person description in JSON, everything below node "profile"

        """

        if 'sex' in r['profile'][0]:
            if r['profile'][0]['sex'] == protAttr:
                return True
            else:
                return False
        else:
            print('>>> undetermined\n')
            return False

    def __determineWorkMonths(self, r):
        """
        takes a person's profile as JSON node and computes the total amount of work months this
        person has

        Parameters:
        ----------
        r : JSON node
        """

        total_working_months = 0  # ..of that profile
        job_duration = 0

        if len(r['profile'][0]) >= 4:  # a job is on the profile
            list_of_Jobs = r['profile'][0]['jobs']
            # print('profile summary' + str(r['profile'][0]['jobs']))
            for count in range(0, len(list_of_Jobs)):
                if len(list_of_Jobs[count]) > 3:  # an exact duration is given at 5 nodes!
                    job_duration_string = list_of_Jobs[count]['jobDates']
                    if job_duration_string == 'bis heute':
                        # print('job with no dates found - will be count for ' + str(job_with_no_dates) + ' months.')
                        job_duration = self.EDUCATION_OR_JOB_WITH_NO_DATES

                    else:
                        job_start_string, job_end_string = job_duration_string.split(' - ')

                        if len(job_start_string) == 4:
                            job_start = datetime.datetime.strptime(job_start_string, "%Y")
                        elif len(job_start_string) == 7:
                            job_start = datetime.datetime.strptime(job_start_string, "%m/%Y")
                        else:
                            print("error reading start date")

                        if len(job_end_string) == 4:
                            job_end = datetime.datetime.strptime(job_end_string, "%Y")
                        elif len(job_end_string) == 7:
                            job_end = datetime.datetime.strptime(job_end_string, "%m/%Y")
                        else:
                            print("error reading end date")

                        if job_end - job_start == 0:
                            delta = self.EDUCATION_OR_JOB_WITH_SAME_YEAR
                        else:
                            delta = job_end - job_start

                        job_duration = math.ceil(delta.total_seconds() / 2629743.83)
                total_working_months += job_duration
        else:
            print('-no jobs on profile-')

        return total_working_months

    def __determineEduMonths(self, r):
        """
        takes a person's profile as JSON node and computes the total amount of work months this
        person has

        Parameters:
        ----------
        r : JSON node
        """

        total_education_months = 0  # ..of that profile
        edu_duration = 0

        if 'education' in r:  # education info is on the profile
            list_of_edu = r['education']  # edu child nodes {institution, url, degree, eduDuration}
            # print('education summary' + str(r['education']))
            for count in range(0, len(list_of_edu)):
                if 'eduDuration' in list_of_edu[count]:  # there are education dates

                    edu_duration_string = list_of_edu[count]['eduDuration']
                    if edu_duration_string == ('bis heute' or None or ''):
                        edu_duration = self.EDUCATION_OR_JOB_WITH_NO_DATES
                    else:
                        edu_start_string, edu_end_string = edu_duration_string.split(' - ')

                        if len(edu_start_string) == 4:
                            edu_start = datetime.datetime.strptime(edu_start_string, "%Y")
                        elif len(edu_start_string) == 7:
                            edu_start = datetime.datetime.strptime(edu_start_string, "%m/%Y")
                        else:
                            print("error reading start date")

                        if len(edu_end_string) == 4:
                            edu_end = datetime.datetime.strptime(edu_end_string, "%Y")
                        elif len(edu_end_string) == 7:
                            edu_end = datetime.datetime.strptime(edu_end_string, "%m/%Y")
                        else:
                            print("error reading end date")

                        if edu_end - edu_start == 0:
                            delta = self.EDUCATION_OR_JOB_WITH_SAME_YEAR
                        else:
                            delta = edu_end - edu_start

                        edu_duration = math.ceil(delta.total_seconds() / 2629743.83)

                        # print(job_duration_string)
                        # print('this job: ' + str(job_duration))

                else:
                    edu_duration = self.EDUCATION_OR_JOB_WITH_NO_DATES

                total_education_months += edu_duration
                # print('total jobs: ' + str(total_working_months))

            # print("studying: " + str(total_education_months))
        else:
            print('-no education on profile-')

        return total_education_months
