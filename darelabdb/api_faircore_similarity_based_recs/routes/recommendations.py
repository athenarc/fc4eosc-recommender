from enum import Enum
from typing import List, Optional

from darelabdb.api_faircore_similarity_based_recs.config_reader import app_config
from darelabdb.api_faircore_similarity_based_recs.db.initialize import get_db
from darelabdb.api_faircore_similarity_based_recs.db.publication import (
    get_publication_preview,
)
from darelabdb.api_faircore_similarity_based_recs.recommender import get_recommendations
from darelabdb.api_faircore_similarity_based_recs.schemas.recommendation import (
    Recommendation,
)
from darelabdb.utils_database_connector.core import Database
from darelabdb.utils_schemas.user_state import UserState
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

router = APIRouter(
    prefix=f"{app_config['FASTAPI']['BASE_URL']}",
    tags=["Recommendations"],
)


class Community(Enum):
    beopen = "beopen"
    dhch = "dh-ch"
    enermaps = "enermaps"
    dariah = "dariah"


class SimilarResultsRequest(BaseModel):
    result_id: str
    num: Optional[int] = 6

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result_id": "doi_dedup___::4f5ad49bfd28fe3b3207b924077e84e9",
                    "num": 6,
                }
            ]
        }
    }


@router.post("/recommend/")
def post_similar_results(
    req_body: SimilarResultsRequest,
    db: Database = Depends(get_db),
) -> List[Recommendation]:
    """
    The endpoint currently returns recommendations for a subset of 1M research products.

    For the rest it will return 404. This is the case until we have a dump of the whole rdgraph and train
    the recommender for the rest of the products.
    """
    logger.info(f"request | similar publications: {req_body}")

    user_state = UserState(viewed_item_id=req_body.result_id)
    recommendations = get_recommendations(user_state, req_body.num)

    if len(recommendations) == 0:
        logger.warning(
            f"No recommendations found in the recommender for {req_body.result_id}."
        )
        raise HTTPException(
            status_code=404,
            detail=f"No recommendations for result_id {req_body.result_id}",
        )

    response_recommendations = []
    for rec in recommendations:
        (
            title,
            result_type,
            publication_date,
            publisher,
            authors,
        ) = get_publication_preview(rec.item_id, db)
        response_recommendations.append(
            Recommendation(
                result_id=rec.item_id,
                result_title=title,
                result_authors=authors,
                result_type=result_type,
                result_publication_date=publication_date,
                result_publisher=publisher,
                similarity_score=rec.score,
            )
        )

    return response_recommendations


class SupportedCommunitiesResponse(BaseModel):
    communities: List[Community]


@router.get("/supported_communities/")
def get_supported_communities() -> SupportedCommunitiesResponse:
    """
    Get the communities supported by the community based recommenders
    """
    logger.info(f"request | supported communities")

    return SupportedCommunitiesResponse(
        communities=[
            Community.beopen,
            Community.dhch,
            Community.enermaps,
        ]
    )
