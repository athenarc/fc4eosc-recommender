import os
from typing import Callable, List, Optional

import pandas as pd
from darelabdb.nlp_embeddings.embedding_methods.SBERTEmbedding import SBERTEmbedding
from darelabdb.nlp_embeddings.embedding_methods.TextEmbeddingMethodABC import (
    TextEmbeddingMethod,
)
from darelabdb.nlp_embeddings.embedding_storage.EmbeddingDB import EmbeddingDB
from darelabdb.nlp_embeddings.embedding_storage.Pgvector import PgVector
from darelabdb.recs_similarity_based.components.logging.LoggerABC import Logger
from darelabdb.recs_similarity_based.components.text_processing.TextProcessor import (
    TextProcessor,
)
from darelabdb.recs_similarity_based.recommenders.filtering import filter_candidates
from darelabdb.utils_schemas.item import Item
from darelabdb.utils_schemas.item_recommendation import ItemRecommendation
from darelabdb.utils_schemas.user_state import UserState
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm


class VectorSearchRecommender:
    def __init__(
        self,
        embedding_db: EmbeddingDB,
        text_embedding_method: Optional[TextEmbeddingMethod] = None,
        recommendations_filtering_methods: Optional[List[Callable]] = None,
        loggers: Optional[List[Logger]] = None,
    ):
        """
        The item-item recommender based on approximate similarity. Responsible for initialising the required managers
        (for the embeddings and the similarities of the items) and providing recommendations based on the user state.

        Args:
            embedding_db: The database that will store the embeddings of the items.
            text_embedding_method: Method that will embed the text attributes of the items.
            recommendations_filtering_methods: A list of filtering methods that will be applied to each item id that is
                candidate for recommendations. Should take as input the id of the item and return True if the item
                should be kept, False otherwise.
            loggers: A list of loggers that will be used to log the recommendations created. Available: StdoutLogger,
                FileLogger, MongoLogger
        """
        self.text_embedding_method = (
            text_embedding_method if text_embedding_method else SBERTEmbedding()
        )

        self.embedding_db = embedding_db
        self.filtering_methods = recommendations_filtering_methods
        self.loggers = loggers

    def update(self, items: List[Item]) -> None:
        """
        Creates and returns the embeddings of a list of items.
        Args:
            items: A list of items from which the embeddings will be created.
        """
        items_text = self._clean_item_texts(items)

        embeddings = self.text_embedding_method.get_embeddings(
            items_text["text"].tolist()
        )

        items_text["embedding"] = embeddings.tolist()
        items_text = items_text.drop(columns=["text"])

        self.embedding_db.populate(
            rows={
                "id": items_text["id"].tolist(),
                "embedding": items_text["embedding"].tolist(),
            },
        )

    def recommend(
        self, user_state: UserState, recs_num: int
    ) -> List[ItemRecommendation]:
        if len(user_state.item_history) > 0:
            # Item history could be supported in the future (but in the scope of Faircore/DataDazzle it will have
            # no impact on the recommendations)
            logger.warning(
                "Item history is not supported by the VectorSearchRecommender. The item history will be ignored"
            )
            user_state.item_history = []

        embedding = self.embedding_db.get_embedding(str(user_state.viewed_item_id))
        if embedding is None:
            logger.warning(
                f"Item with id {user_state.viewed_item_id} does not exist in the VectorSearchRecommender's database."
            )
            return []

        # We ask for an extra neighbor (recs_num + 1) to remove the viewed item from the recommendations
        candidates = self.embedding_db.get_neighbors(
            embedding, columns=["id"], num=recs_num + 1
        ).set_index("id")["similarity"]

        try:
            candidates = candidates.drop(user_state.viewed_item_id)
        except KeyError:
            candidates = candidates.iloc[:-1]

        if self.filtering_methods is not None:
            # Filter out items that do not pass the filtering methods
            candidates = filter_candidates(candidates, self.filtering_methods)

        # Order item by similarity score
        candidates = candidates.sort_values(ascending=False)

        recommendations = [
            ItemRecommendation(item_id=item_id, score=similarity_score)
            for item_id, similarity_score in candidates[:recs_num].items()
        ]

        self._log(user_state=user_state, recommendations=recommendations)

        return recommendations

    def _log(self, user_state: UserState, recommendations: List[ItemRecommendation]):
        if self.loggers is not None:
            for log in self.loggers:
                log.log_item_recommendation(
                    user_state=user_state, recommendations=recommendations
                )

    def _clean_item_texts(self, items: List[Item]) -> pd.DataFrame:
        extra_cleaning_rules = {"..": ".", "-": " ", "*": ""}
        items_text = pd.DataFrame.from_records(
            [
                {
                    "id": item.item_id,
                    "text": TextProcessor.clean_text(
                        " ".join(item.text_attributes.values()),
                        extra_rules=extra_cleaning_rules,
                    ),
                }
                for item in tqdm(
                    items, desc="Preprocessing text attributes", mininterval=180
                )
            ]
        )
        return items_text


if __name__ == "__main__":
    load_dotenv()

    embedding_db = PgVector(
        db_name="fc4eosc",
        host="train.darelab.athenarc.gr",
        port="5555",
        user=os.getenv("DATABASE_FC4EOSC_USERNAME"),
        password=os.getenv("DATABASE_FC4EOSC_PASSWORD"),
        primary_key_col_name="id",
        embedding_col_name="embedding",
        schema_name="item_embeddings_test",
        table_name="items",
        column_types={
            "nl_question": "TEXT",
            "sql_query": "TEXT",
            "embedding": "vector(384)",
        },
    )
    rec = VectorSearchRecommender(embedding_db=embedding_db)
    # item_test = [
    #     Item(
    #         item_id=str(ind),
    #         text_attributes={"text": "This is a test", "title": "Test"},
    #     )
    #     for ind in range(10_000)
    # ]

    # items = [
    #     Item(item_id="1", text_attributes={"text": "This is a test", "title": "Test"}),
    #     Item(
    #         item_id="2",
    #         text_attributes={"text": "This is another test", "title": "Test"},
    #     ),
    #     Item(item_id="3", text_attributes={"text": "I am Mike", "title": "Name"}),
    #     Item(item_id="4", text_attributes={"text": "She is Anna", "title": "Test"}),
    #     Item(item_id="5", text_attributes={"text": "This is a test", "title": "Test"}),
    # ]
    #
    # rec.update(items)

    print(
        rec.recommend(
            UserState(
                viewed_item_id="5",
                item_history=[],
            ),
            recs_num=6,
        )
    )
