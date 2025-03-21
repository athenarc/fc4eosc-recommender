from enum import Enum
from typing import List, Literal, Optional


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from darelabdb.utils_database_connector.core import Database
from darelabdb.utils_configs.apis.faircore_mabrecs import settings
from darelabdb.api_faircore_mabrecs.api import (
    MABRecommend,
    MABUpdate,
    MAB_recommend,
    MAB_update,
)

router = APIRouter(prefix=settings.base_path)


class Community(Enum):
    beopen = "beopen"
    dhch = "dh-ch"
    enermaps = "enermaps"
    eosc = "eosc"


@router.get(settings.get_communities)
async def available_communities():
    return [community.value for community in Community]


class Recommend(BaseModel):
    community: Community
    top_k_fields: int = Field(
        default=3,
        description="The number of fields to recommend",
    )
    top_k_publications: int = Field(
        default=5,
        description="The number of recommendations per field",
    )
    user: str | None = None
    update: bool = Field(
        default=True,
        title="Update MABs",
        description="Use False in case of testing/dev",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "community": "beopen",
                "top_k_fields": 2,
                "top_k_publications": 2,
                "user": "1823219319238u1923441237",
            }
        }


class Item(BaseModel):
    result_id: str
    result_title: str
    result_country: str | None
    result_authors: str
    result_publication_date: str
    result_publisher: str | None


class Recommendations(BaseModel):
    field: str
    recommendations: List[Item]

    class Config:
        json_schema_extra = {
            "example": [
                {
                    "field": "Climate change",
                    "recommendations": [
                        {
                            "result_id": "50|doi_dedup___::2a2d376d9ed8688c9d5aaca6fcd3294d",
                            "result_title": "Ecosystem recovery after climatic extremes enhanced by genotypic diversity",
                            "result_country": "DE",
                            "result_authors": "A. Hämmerli,Anneli Ehlers,Thorsten B. H. Reusch,Boris Worm",
                            "result_publication_date": "2005-02-14",
                            "result_publisher": "Proceedings of the National Academy of Sciences",
                        },
                        {
                            "result_id": "50|doi_dedup___::b34227c2436283898ff20177ce5f94aa",
                            "result_title": "Evolution in an acidifying ocean",
                            "result_country": "DE",
                            "result_authors": "Philip L. Munday,Sam Dupont,Jonathon H. Stillman,Thorsten B. H. Reusch,Jonathon H. Stillman,Piero Calosi,Jennifer M. Sunday",
                            "result_publication_date": "2014-02-01",
                            "result_publisher": "",
                        },
                    ],
                },
                {
                    "field": "Greenhouse gas",
                    "recommendations": [
                        {
                            "result_id": "50|doi_________::444b3c0ffd052615596c5fe8cedafcbc",
                            "result_title": "Combined application of multi-criteria optimization and life-cycle sustainability assessment for optimal distribution of alternative passenger cars in U.S.",
                            "result_country": "",
                            "result_authors": "Murat Kucukvar,Omer Tatari,Qipeng P. Zheng,Nuri Cihat Onat",
                            "result_publication_date": "2016-01-01",
                            "result_publisher": "Elsevier BV",
                        },
                        {
                            "result_id": "50|doi_________::49f0028f8110e603553a3d5d7aeda9e2",
                            "result_title": "A comprehensive model of regional electric vehicle adoption and penetration",
                            "result_country": "",
                            "result_authors": "Roxana J. Javid,Ali Nejat",
                            "result_publication_date": "2017-02-01",
                            "result_publisher": "Elsevier BV",
                        },
                    ],
                },
            ]
        }


@router.post(
    settings.recommend,
    response_model=List[Recommendations],
)
async def recommend(recommend: Recommend):

    rec = MABRecommend(
        input=recommend.community.value,
        top_k_categories=recommend.top_k_fields,
        top_k_items=recommend.top_k_publications,
        user=recommend.user,
        update=recommend.update,
    )

    cats, ids_str = MAB_recommend(settings, rec)
    recommendations = []

    query = f"""
        SELECT 
            id as result_id, 
            title as result_title, 
            country as result_country, 
            case when authors is null then '' else authors end as result_authors,
            publication_date as result_publication_date, 
            publisher as result_publisher
        FROM recsys_schema.top100_per_level_2_fos
        WHERE id IN ({ids_str})
    """
    results = Database("fc4eosc").execute(query, fix_dates=True, limit=1000)
    if "error" in results:
        raise HTTPException(status_code=503, detail=results["error"])

    for category in cats:
        pubs = []
        for id in cats[category]:
            pubs.append(
                results[results["result_id"] == id].to_dict(orient="records")[0]
            )
        recommendations.append({"field": category, "recommendations": pubs})

    return recommendations


class Update(BaseModel):
    community: Community
    category: str
    publication: str = Field(title="Publication DOI")
    reward: Literal[-1, 1] = 1
    user: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "community": "beopen",
                "category": "Fuel efficiency",
                "publication": "50|doi_dedup___::2a2d376d9ed8688c9d5aaca6fcd3294d",
                "user": "1823219319238u1923441237",
            }
        }


@router.post(settings.update)
async def update(update: Update):
    upd = MABUpdate(
        input=update.community.value,
        category=update.category,
        item=update.publication,
        reward=update.reward,
        user=update.user,
    )
    return MAB_update(settings, upd)
