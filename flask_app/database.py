from mongoengine import *

"""
Definition of the MongoDB data structure. 
"""
class DocRepr(DynamicDocument):
    meta = {
        'collection': 'documents'
    }
    _id = ObjectIdField()


class PreDocRepr(DynamicEmbeddedDocument):
    _id = ObjectIdField()
    ranking_type = StringField(default="")


class Ranking(DynamicEmbeddedDocument):
    _id = ObjectIdField()
    docs = ListField()
    ranking_type = StringField(default="")


class QueryRepr(Document):
    meta = {
        'collection': 'queries'
    }
    _id = ObjectIdField()
    title = StringField(default="")
    text = StringField(default="")


class Data(Document):
    meta = {
        'collection': 'dataset'
    }
    _id = ObjectIdField()
    query = StringField(default="")
    rankings = EmbeddedDocumentListField(Ranking)


class Task(DynamicDocument):
    meta = {
        'collection': 'tasks'
    }
    _id = ObjectIdField()
    data = StringField(default="")
    ranking_type = StringField(default="")
    setting = StringField(default="")


class TaskCompare(DynamicDocument):
    meta = {
        'collection': 'tasks_compare'
    }
    _id = ObjectIdField()
    data = StringField(default="")
    ranking_type_1 = StringField(default="")
    ranking_type_2 = StringField(default="")
    setting = StringField(default="")


class TaskScore(DynamicDocument):
    meta = {
        'collection': 'tasks_score'
    }
    _id = ObjectIdField()
    data = StringField(default="")
    index = StringField(default="")
    setting = StringField(default="")


class Experiment(Document):
    meta = {
        'collection': 'experiments'
    }
    _id = ObjectIdField()
    _exp_id = StringField(required=True)
    _description = StringField(default="")
    tasks = ListField()


class Interaction(EmbeddedDocument):
    doc_id = StringField(default="")
    n_views = StringField(default="")
    timestamps = ListField()
    shortlisted = StringField(default="")


class InteractionCompare(EmbeddedDocument):
    ranking_type_1 = StringField(default="")
    ranking_type_2 = StringField(default="")
    selected_ranking = StringField(default="")


class InteractionScore(EmbeddedDocument):
    doc = StringField(default="")
    query = StringField(default="")
    score = StringField(default="")


class TaskVisited(EmbeddedDocument):
    task = StringField(required=True)
    exp = StringField(required=True)
    interaction_compare = EmbeddedDocumentField(InteractionCompare, default=InteractionCompare())
    interaction_score = EmbeddedDocumentField(InteractionScore, default=InteractionScore())
    interactions = EmbeddedDocumentListField(Interaction)
    order_checkbox = ListField()


class User(DynamicDocument):
    meta = {
        'collection': 'users'
    }
    _id = ObjectIdField()
    _user_id = StringField(required=True)
    _attention_check = StringField(default="")
    tasks_visited = EmbeddedDocumentListField(TaskVisited)




def create_collections():
    db = get_db()

    if 'users' not in db.list_collection_names():
        dummy_document = User(_user_id="dummy--")
        dummy_document.save()
        User.objects().delete()
    if 'dataset' not in db.list_collection_names():
        dummy_document = Data()
        dummy_document.save()
        Data.objects().delete()
    if 'documents' not in db.list_collection_names():
        dummy_document = DocRepr()
        dummy_document.save()
        DocRepr.objects().delete()
    if 'queries' not in db.list_collection_names():
        dummy_document = QueryRepr()
        dummy_document.save()
        QueryRepr.objects().delete()
    if 'tasks_compare' not in db.list_collection_names():
        dummy_document = TaskCompare()
        dummy_document.save()
        TaskCompare.objects().delete()
    if 'tasks' not in db.list_collection_names():
        dummy_document = Task()
        dummy_document.save()
        Task.objects().delete()
    if 'tasks_score' not in db.list_collection_names():
        dummy_document = TaskScore()
        dummy_document.save()
        TaskScore.objects().delete()
    if 'experiment' not in db.list_collection_names():
        dummy_document = Experiment(_exp_id="dummy--")
        dummy_document.save()
        Experiment.objects().delete()