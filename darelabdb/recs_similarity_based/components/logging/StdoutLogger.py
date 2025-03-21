import json
from typing import Dict, List

from darelabdb.recs_similarity_based.components.logging.LoggerABC import Logger
from darelabdb.recs_similarity_based.components.logging.utils import get_timestamp
from darelabdb.utils_schemas.field_recommendation import FieldRecommendation
from darelabdb.utils_schemas.item_recommendation import ItemRecommendation
from darelabdb.utils_schemas.user_state import UserState
from loguru import logger


class StdoutLogger(Logger):
    """
    Logs the recommendations to stdout in a json string format.
    """

    def __init__(self, recommender_id: str = None):
        self.recommender_id = recommender_id if recommender_id is not None else ""

    def log_item_recommendation(
        self, user_state: UserState, recommendations: List[ItemRecommendation]
    ) -> None:
        recommendation_state = {
            "recommender_id": self.recommender_id,
            "user_state": dict(user_state),
            "recommendations": [
                dict(recommendation) for recommendation in recommendations
            ],
            "timestamp": get_timestamp(),
        }

        logger.info(json.dumps(recommendation_state))

    def log_field_recommendation(
        self,
        text_attributes: Dict[str, str],
        recommendations: List[FieldRecommendation],
    ) -> None:
        recommendation_state = {
            "recommender_id": self.recommender_id,
            "text_attributes": text_attributes,
            "recommendations": [
                dict(recommendation) for recommendation in recommendations
            ],
            "timestamp": get_timestamp(),
        }

        logger.info(json.dumps(recommendation_state))
