import os
from typing import List

from darelabdb.api_faircore_similarity_based_recs.config_reader import app_config
from darelabdb.nlp_embeddings.embedding_storage.Pgvector import PgVector
from darelabdb.recs_similarity_based import ApproximateSimilarityItemRecommender
from darelabdb.recs_similarity_based.recommenders.vector_search_recommender import (
    VectorSearchRecommender,
)
from darelabdb.utils_cache.Mongo import MongoCache
from darelabdb.utils_cache.Postgres import PostgresCache
from darelabdb.utils_schemas.item_recommendation import ItemRecommendation
from darelabdb.utils_schemas.user_state import UserState
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# Will uncomment when the recommender is trained on the new dump
# similarities_cache_manager = PostgresCache(
# db_name=app_config["RECOMMENDER_DATABASE_GOLD"]["DB_NAME"],
# specific_schema=app_config["RECOMMENDER_DATABASE_GOLD"]["SCHEMA_NAME"],
# )

similarities_cache_manager = MongoCache(
    host=app_config["RECOMMENDER_DATABASE_GOLD"]["HOST"],
    port=app_config["RECOMMENDER_DATABASE_GOLD"]["PORT"],
    username=app_config["RECOMMENDER_DATABASE_GOLD"]["USERNAME"],
    password=app_config["RECOMMENDER_DATABASE_GOLD"]["PASSWORD"],
    db_name=app_config["RECOMMENDER_DATABASE_GOLD"]["DB_NAME"],
)

gold_recommender = ApproximateSimilarityItemRecommender(
    recommender_id="faircore_similarity_based_rs",
    similarities_cache_manager=similarities_cache_manager,
    inference_only=True,
)


embedding_db = PgVector(
    db_name=app_config["RECOMMENDER_DATABASE_SILVER"]["DB_NAME"],
    host=app_config["RECOMMENDER_DATABASE_SILVER"]["HOST"],
    port=app_config["RECOMMENDER_DATABASE_SILVER"]["PORT"],
    user=os.getenv("DATABASE_FC4EOSC_USERNAME"),
    password=os.getenv("DATABASE_FC4EOSC_PASSWORD"),
    schema_name=app_config["RECOMMENDER_DATABASE_SILVER"]["SCHEMA_NAME"],
    table_name=app_config["RECOMMENDER_DATABASE_SILVER"]["TABLE_NAME"],
    column_types={
        "id": "TEXT",
        "embedding": f"vector({app_config['RECOMMENDER_DATABASE_SILVER']['EMBEDDING_DIM']})",
    },
    primary_key_col_name="id",
    embedding_col_name="embedding",
)

silver_recommender = VectorSearchRecommender(embedding_db=embedding_db)


def get_recommendations(user_state: UserState, num: int) -> List[ItemRecommendation]:
    """
    Get recommendations for a given result_id.

    Args:
        user_state: Class containing the viewed item id.
        num: Number of recommendations to return.

    Returns:
        A list of recommendations.
    """
    recommendations = gold_recommender.recommend(user_state, num)

    if len(recommendations) == 0:
        logger.info(
            f"No recommendations found in the gold recommender for {user_state.viewed_item_id}. "
            f"Using the silver recommender."
        )
        recommendations = silver_recommender.recommend(user_state, num)

    recommendations = sorted(recommendations, key=lambda x: x.score, reverse=True)

    return recommendations
