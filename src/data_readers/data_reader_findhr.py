import os
import pandas as pd
import json
import ast
from data_readers.data_reader import DataReader


def clean_text(text, upper=False):
    text = str(text).replace('_', ' ').replace('*', '').replace('!', '')
    if upper:
        return text.upper()
    return text.strip()


def parse_frozenset_str(s: str):
    if not isinstance(s, str) or 'frozenset' not in s:
        return [s]
    try:
        set_str = s.replace('frozenset(', '', 1)[:-1]
        evaluated = ast.literal_eval(set_str)
        if isinstance(evaluated, (set, frozenset)):  # Aggiunto frozenset per robustezza
            return list(evaluated)
    except (ValueError, SyntaxError):
        pass
    return [s]


def candidate_to_text(candidate: pd.DataFrame) -> pd.DataFrame:
    if 'Gender' in candidate.columns:
        candidate['Gender_display'] = candidate['Gender'].apply(lambda x: 'Male' if x == 1 else 'Female')

    for col in ["Job and Language Skills"]:
        val = candidate[col].iloc[0]
        if col in candidate.columns and val is not None and pd.notna(val).any():
            if col == "factual_xai" or col == "counterfactual_xai":
                continue

            if isinstance(candidate[col].iloc[0], list):
                items = candidate[col].iloc[0]
            else:
                items = parse_frozenset_str(candidate[col].iloc[0])

            if all(isinstance(item, str) for item in items):
                candidate[col + "_display"] = ', '.join(sorted(items))
            else:
                candidate[col + "_display"] = str(items[0]) if items else ''

    return candidate


def query_to_text(query: pd.DataFrame) -> str:
    query_text = ""
    for col in query.columns:
        if col in ['id_j', 'min_years_exp_int_j', 'title', 'driving_license_j']:
            continue

        col_cleaned = clean_text(col.replace('_j', ''))
        query_text += f"*{col_cleaned.upper()}*\n"
        value = query[col].iloc[0]

        if isinstance(value, str) and value.startswith('frozenset'):
            items = parse_frozenset_str(value)
            query_text += clean_text(', '.join(sorted(items))) + '\n\n'
        else:
            query_text += clean_text(str(value)) + '\n\n'

    return query_text


def transform_data_xai(candidate_data: dict, dir_name: str):
    if 'factual_image' in candidate_data and candidate_data['factual_image']:
        base_name = os.path.basename(candidate_data['factual_image'])
        candidate_data['factual_image'] = os.path.join(dir_name, 'images', base_name)
    if 'image_xai' in candidate_data and candidate_data['image_xai']:
        for item in candidate_data['image_xai']:
            base_name = os.path.basename(item['image'])
            item['image'] = os.path.join(dir_name, 'images', base_name)
    if 'factual_xai' in candidate_data and isinstance(candidate_data['factual_xai'], list):
        for item in candidate_data['factual_xai']:
            if 'factual_image' in item and item['factual_image']:
                base_name = os.path.basename(item['factual_image'])
                item['factual_image'] = os.path.join(dir_name, 'images', base_name)
            if 'data' in item and item['data']:
                for key, val in item['data'].items():
                    if isinstance(val, (int, float)):
                        item['data'][key] = round(val, 3)


    return candidate_data


class DataReaderFindhr(DataReader):

    def __init__(self, configs):
        super().__init__(configs)

    def transform_data(self):
        """
        Trasforma i dati del dataset findhr in DataFrame pandas.
        """
        occupation_dirs = [d for d in os.listdir(os.path.join(self.data_path, "data")) if
                           os.path.isdir(os.path.join(self.data_path, "data", d))]

        dataframes_occupations = []
        dataframes_candidates = []


        field_rename_map = {
            "id_j": "id_j",
            "occupation_j": "Occupation_description_j",
            "working_hours_j": "Full/Part-time_j",
            "driving_license_j": "driving_license_j",
            "min_edu_eqf_j": "education_eqf_level_required_j",
            "min_years_exp_j": "minimum_years_of_experience_required_j",
            "skills_req_j": "skills_required_j",
            "lang_skills_j": "language_skills_required_j",
            "permanent_j": "Permanent/Fixed-term_j",
            "min_years_exp_int_j": "min_years_exp_int_j"
        }

        for dir_name in occupation_dirs:
            desc_path = os.path.join(self.data_path, "data", dir_name, 'description.json')
            if not os.path.exists(desc_path):
                continue

            with open(desc_path, 'r', encoding='utf-8') as f:
                query_data = json.load(f)

            renamed_query_data = {}
            for old_key, new_key in field_rename_map.items():
                if old_key in query_data:
                    renamed_query_data[new_key] = query_data[old_key]
                else:
                    pass

            query_df = pd.json_normalize(renamed_query_data)

            query_df['title'] = dir_name
            query_df['text'] = query_to_text(query_df)
            dataframes_occupations.append(query_df)

            json_files = [f for f in os.listdir(os.path.join(self.data_path, "data", dir_name)) if
                          f.endswith('.json') and f != 'description.json']
            print(f"File JSON candidati trovati in {dir_name}: {json_files}")
            for file_name in json_files:
                file_path = os.path.join(self.data_path, "data", dir_name, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    candidate_data = json.load(f)
                print(file_name)
                candidate_data = transform_data_xai(candidate_data, dir_name)
                candidate_df = pd.json_normalize(candidate_data)
                candidate_df = candidate_to_text(candidate_df)
                candidate_df['query'] = dir_name

                dataframes_candidates.append(candidate_df)


        data_test = pd.concat(dataframes_candidates, ignore_index=True)
        data_train = data_test
        dataframe_occupations = pd.concat(dataframes_occupations, ignore_index=True)

        return dataframe_occupations, data_train, data_test
