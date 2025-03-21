import json
from pathlib import Path
from typing import Dict, List

from darelabdb.recs_similarity_based.components.logging.LoggerABC import Logger
from darelabdb.recs_similarity_based.components.logging.utils import get_timestamp
from darelabdb.utils_schemas.field_recommendation import FieldRecommendation
from darelabdb.utils_schemas.item import Item
from darelabdb.utils_schemas.item_recommendation import ItemRecommendation
from darelabdb.utils_schemas.user_state import UserState
from loguru import logger


class FileLogger(Logger):
    """
    Logs the recommendations to a file in a .jsonl (json lines) format.
    """

    def __init__(self, file_path: str, recommender_id: str = None):
        self.recommender_id = recommender_id if recommender_id is not None else ""
        if Path(file_path).is_file():
            logger.info(f"Logging file {file_path} already exists. Appending to it.")
        else:
            logger.info(
                f"Logging file {file_path} does not exist. Will be created upon first log."
            )

        self.file_path = file_path

    def _save_record(self, record: Dict) -> None:
        with open(self.file_path, "a") as f:
            f.write(json.dumps(record) + "\n")

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

        self._save_record(recommendation_state)

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

        self._save_record(recommendation_state)
