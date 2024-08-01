
from rankers.ranker_ranklib import RankLibRanker
from fairness_interventions.fairness_method_CIFRank import CIFRank
from fairness_interventions.fairness_method_FAIR import FAIRRanking

fairness_method_mapping = {
    'CIFRank': CIFRank,
    'FA*IR': FAIRRanking,
}

ranker_mapping = {
    'Ranklib': RankLibRanker,
}