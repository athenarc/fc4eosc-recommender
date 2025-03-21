from typing import Dict, List

import pymongo
from darelabdb.recs_similarity_based.components.logging.LoggerABC import Logger
from darelabdb.recs_similarity_based.components.logging.utils import get_timestamp
from darelabdb.utils_schemas.field_recommendation import FieldRecommendation
from darelabdb.utils_schemas.item import Item
from darelabdb.utils_schemas.item_recommendation import ItemRecommendation
from darelabdb.utils_schemas.user_state import UserState


class MongoLogger(Logger):
    """
    Logs the recommendations to a mongo collection following the schema:
    ```
    {
        "user_state": {
            "viewed_item_id": 1,
            "item_history": [2, 3, 4]
        },
        "recommendations": [
            {"item_id": 5, "score": 0.5}, {"item_id": 6, "score": 0.2}
        ]
    }
    ```
    """

    def __init__(
        self,
        host: str,
        port: int,
        recommender_id: str = None,
        username: str = "",
        password: str = "",
        db_name: str = "similarity_rs",
        logs_collection_name: str = "recommendation_logs",
    ):
        self.recommender_id = recommender_id if recommender_id is not None else ""
        self.mongo_url = self._form_mongo_url(username, password, host, port)
        self.db_name = db_name
        self.logs_collection_name = logs_collection_name

    @staticmethod
    def _form_mongo_url(username, password, host, port) -> str:
        uri = f"mongodb://{username}:{password}@" if username and password else ""
        uri += f"{host}:{port}"
        return uri

    def _save_record(self, record: Dict) -> None:
        with pymongo.MongoClient(self.mongo_url) as connector:
            connector[self.db_name][self.logs_collection_name].insert_one(record)

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
