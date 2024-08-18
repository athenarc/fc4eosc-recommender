import os
import logging
from typing import List, Dict
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum

from database.utils_database_connector.core import Database
from database.rec_data import get_recommendations_by_author

app = FastAPI(
    openapi_url= "/crps-rec/openapi.json",
    docs_url="/crps-rec/docs",
    redoc_url= "/crps-rec/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define available communities as an enum
class AvailableCommunities(str, Enum):
    beopen = "beopen"
    dariah = "dariah"
    dh_ch = "dh-ch"
    enermaps = "enermaps"
    eosc = "eosc"

class RecommendationResponse(BaseModel):
    recommendations: Dict[str, List[Dict[str, str]]] = Field(
        ...,
        example={
            "beopen": [
                {
                    "result_id": "doi_dedup___::9816848a0b623505f722f58c7b94fb9b",
                    "result_title": "A simultaneous approach for optimal allocation of renewable energy sources and electric vehicle charging stations in smart grids based on improved GA-PSO algorithm",
                    "result_type": "publication",
                    "result_publication_date": "2017-07-01",
                    "result_publisher": "Elsevier BV"
                },
                {
                    "result_id": "doi_dedup___::2f978b9e0087e219d11fae7275cbef59",
                    "result_title": "Modeling and forecasting building energy consumption: A review of data-driven techniques",
                    "result_type": "publication",
                    "result_publication_date": "2019-07-01",
                    "result_publisher": "Elsevier BV"
                }
            ],
            "enermaps": [
                {
                    "result_id": "doi_dedup___::b6e8f431d0b45a7492b9f74c0f52e129",
                    "result_title": "Designing microgrid energy markets",
                    "result_type": "publication",
                    "result_publication_date": "2018-01-01",
                    "result_publisher": "Elsevier BV"
                },
                {
                    "result_id": "doi_dedup___::09c04c282d79fa77f66c1f2966f0700d",
                    "result_title": "Peer-to-peer and community-based markets: A comprehensive review",
                    "result_type": "publication",
                    "result_publication_date": "2019-04-01",
                    "result_publisher": "Elsevier BV"
                }
            ]
        }
    )

class RecommendRequest(BaseModel):
    author_id: str = Field(
        ...,
        example="0000-0002-6123-1086"
    )

@app.get("/api/faircore/user-to-item-recommender/available-communities", response_model=List[str], summary="Get Available Communities", description="Endpoint to get the list of available communities.")
async def available_communities():
    """
    Endpoint to get the list of available communities.
    """
    return [community.value for community in AvailableCommunities]

@app.post("/api/faircore/user-to-item-recommender/recommend",
          response_model=RecommendationResponse,
          summary="Get Recommendations",
          description="Get recommendations per community for a specific author based on their ORCID. Recommendations' number is fixed to 20.")
async def recommend(request: RecommendRequest = Body(...)):
    db = Database("fc4eosc")
    try:
        df = get_recommendations_by_author(db, request.author_id)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No recommendations found for the given ORCID.")

        # Convert the result_publication_date to string
        df['result_publication_date'] = df['result_publication_date'].astype(str)

        # Group by community and convert to list of records
        grouped = df.groupby('community_acronym', group_keys=False).apply(
            lambda x: x.to_dict(orient='records'),
            include_groups=False
        ).to_dict()

        # Convert to desired format
        result_json = {community: records for community, records in grouped.items()}

        return RecommendationResponse(recommendations=result_json)

    except HTTPException as e:
        logging.error(f"HTTP error occurred: {e.detail}")
        raise
    except Exception as e:
        logging.error(f"Error fetching recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    # # Test the API using curl

    # # curl -X GET "http://0.0.0.0:8000/api/faircore/user-to-item-recommender/available-communities"
    # # curl -X POST "http://0.0.0.0:8000/api/faircore/user-to-item-recommender/recommend" -H "Content-Type: application/json" -d '{"author_id": "0000-0002-6123-1086"}'