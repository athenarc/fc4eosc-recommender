from enum import Enum
from typing import List, Literal


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from darelabdb.utils_database_connector.core import Database
from darelabdb.utils_configs.apis.datadazzle_mabrecs import settings
from darelabdb.api_faircore_mabrecs.api import (
    MABRecommend,
    MABUpdate,
    MAB_recommend,
    MAB_update,
)

router = APIRouter()


class Category(Enum):
    agricultural = "agricultural and veterinary sciences"
    engineering = "engineering and technology"
    humanities = "humanities and the arts"
    medical = "medical and health sciences"
    natural = "natural sciences"
    social = "social sciences"


@router.get(settings.get_categories)
async def get_categories():
    return [cat.value for cat in Category]


class Recommend(BaseModel):
    level_1: Category
    top_k_categories: int = Field(
        default=3,
        description="The number of level 2 categories to recommend",
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
                "level_1": "engineering and technology",
                "top_k_categories": 2,
                "top_k_publications": 2,
                "user": "42",
            }
        }


class Item(BaseModel):
    result_id: str
    result_title: str
    result_country: str | None
    result_authors: str
    result_publication_date: str
    result_publisher: str | None
    sk_id: int


class Recommendations(BaseModel):
    category: str
    recommendations: List[Item]

    class Config:
        json_schema_extra = {
            "example": [
                {
                    "category": "chemical engineering",
                    "recommendations": [
                        {
                            "result_id": "doi_dedup___::556fa1d6eca6a7a74e1a0bbd12ed64c3",
                            "result_title": "Structure and activity relationships for amine-based CO2 absorbents-II",
                            "result_country": "NL",
                            "result_authors": "Singh, P.,Niederer, J. P. M.,Versteeg, G. F.",
                            "result_publication_date": "01/04/2007",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 1655,
                        },
                        {
                            "result_id": "doi_dedup___::fc23542f5daee808b6abeeaacc4f99d6",
                            "result_title": "Review of integrity of existing wells in relation to CO2 geological storage: What do we know?",
                            "result_country": None,
                            "result_authors": "Stefan Bachu,Min Zhang",
                            "result_publication_date": "01/07/2011",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 10762224,
                        },
                        {
                            "result_id": "doi_dedup___::a17440b54e34910887248c2278a9288e",
                            "result_title": "CO2 sequestration in depleted oil and gas reservoirscaprock characterization and storage capacity",
                            "result_country": None,
                            "result_authors": "Mingzhe Dong,Zhaowen Li,Sam Huang,Shuliang Li",
                            "result_publication_date": "01/07/2006",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 10716368,
                        },
                        {
                            "result_id": "doi_dedup___::11183b175c2b7e20bc560daee596be22",
                            "result_title": "Separation and Capture of CO<sub>2</sub>from Large Stationary Sources and Sequestration in Geological FormationsCoalbeds and Deep Saline Aquifers",
                            "result_country": None,
                            "result_authors": "Henry W. Pennline,Evan J. Granite,James S. Hoffman,Brian R. Strazisar,Curt M. White",
                            "result_publication_date": "01/06/2003",
                            "result_publisher": "Informa UK Limited",
                            "sk_id": 10564138,
                        },
                        {
                            "result_id": "doi_dedup___::caea99c7f9f14ccaf2d01ee282073d8e",
                            "result_title": "Understanding ethanolamine (MEA) and ammonia emissions from amine based post combustion carbon capture: Lessons learned from field tests",
                            "result_country": None,
                            "result_authors": "Mertens, Jan,Marie-Laure Thielens,Dominique Desagher,Hélène Lepaumier",
                            "result_publication_date": "01/03/2013",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 10233801,
                        },
                    ],
                },
                {
                    "category": "other engineering and technologies",
                    "recommendations": [
                        {
                            "result_id": "doi_dedup___::842cdcb994d2f3b855ab90dc47837b4c",
                            "result_title": "Preparing a nation for autonomous vehicles: opportunities, barriers and policy recommendations",
                            "result_country": None,
                            "result_authors": "Kara M. Kockelman,Kara M. Kockelman,Daniel J. Fagnant,Daniel J. Fagnant",
                            "result_publication_date": "01/07/2015",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 2361,
                        },
                        {
                            "result_id": "doi_dedup___::fd485e1a21252da9d1401d02613bac7d",
                            "result_title": "Biomass pretreatment: Fundamentals toward application",
                            "result_country": None,
                            "result_authors": "Valery Agbor,Nazim Cicek,David B. Levin,Alex Berlin,Richard Sparling",
                            "result_publication_date": "01/11/2011",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 11767288,
                        },
                        {
                            "result_id": "doi_dedup___::f00b73e88e6cc31895b96069c8653f96",
                            "result_title": "A review on energy conservation in building applications with thermal storage by latent heat using phase change materials",
                            "result_country": None,
                            "result_authors": "Mohammed Farid,Amar M. Khudhair",
                            "result_publication_date": "01/01/2004",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 11094907,
                        },
                        {
                            "result_id": "doi_dedup___::27698af11238224b60f5aaf960cfd759",
                            "result_title": "A review on buildings energy consumption information",
                            "result_country": "ES",
                            "result_authors": "Pérez-Lombard, Luis,Pérez-Lombard, Luis,Ortiz, José,Ortiz, José,Pout, Christine,Pout, Christine",
                            "result_publication_date": "01/01/2008",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 10893385,
                        },
                        {
                            "result_id": "doi_dedup___::30cec51178e99ed8896190b0c5ed5d91",
                            "result_title": "Modeling daylight availability and irradiance components from direct and global irradiance",
                            "result_country": "CH",
                            "result_authors": "Joseph J. Michalsky,Joseph J. Michalsky,Pierre Ineichen,Pierre Ineichen,Ronald Stewart,Ronald Stewart,R. Seals,R. Seals,Richard Perez,Richard Perez",
                            "result_publication_date": "01/01/1990",
                            "result_publisher": "Elsevier BV",
                            "sk_id": 10037290,
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
        input=recommend.level_1.value,
        top_k_categories=recommend.top_k_categories,
        top_k_items=recommend.top_k_publications,
        user=recommend.user,
        update=recommend.update,
    )

    cats, ids_str = MAB_recommend(settings, rec)

    recommendations = []
    query = f"""
        SELECT distinct sk_id, id as result_id, title as result_title, country as result_country, authors as result_authors, publication_date as result_publication_date, publisher as result_publisher
        FROM recsys_schema.top100_per_level_2_fos
        WHERE sk_id IN ({ids_str})
    """
    results = Database("fc4eosc").execute(query, fix_dates=True, limit=1000)
    if "error" in results:
        raise HTTPException(status_code=503, detail=results["error"])

    for category in cats:
        pubs = []
        for id in cats[category]:
            pubs.append(results[results["sk_id"] == id].to_dict(orient="records")[0])
        recommendations.append({"category": category, "recommendations": pubs})

    return recommendations


class Update(BaseModel):
    level_1: Category
    level_2: str
    publication: int = Field(title="Publication SK ID")
    reward: Literal[-1, 1] = 1
    user: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "level_1": "engineering and technology",
                "level_2": "chemical engineering",
                "publication": 1655,
                "user": "42",
            }
        }


@router.post(settings.update)
async def update(update: Update):
    upd = MABUpdate(
        input=update.level_1.value,
        category=update.level_2,
        item=update.publication,
        reward=update.reward,
        user=update.user,
    )
    return MAB_update(settings, upd)
