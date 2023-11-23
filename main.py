
import functools
import logging
import os
import pickle
from enum import Enum
from typing import Union, List

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, Path, Query, HTTPException
from pydantic import BaseModel
from scipy.sparse import load_npz

from src.helpers.db_interactions import *
from src.api.api_responses import RECOMMENDATION_RESPONSES, NEIGHBOR_RESPONSES

logging.basicConfig(level=logging.INFO)

load_dotenv()  # Load the .env file

# Fetch environment variables based on .env file structure
db_host = os.getenv('HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('PASSWORD')
db_port = os.getenv('PORT')

app = FastAPI(
    openapi_url= "/crps-rec/openapi.json",
    docs_url="/crps-rec/docs",
    redoc_url= "/crps-rec/redoc",
)

class AvailableCommunities(str, Enum):
    zbmath = "zbMATH"
    transport = "Transport Research"
    humanities = "Digital Humanities and Cultural Heritage"
    energy = "Energy Research"

class RecommendationResponse(BaseModel):
    recommendations: List[Union[int, str]]

class NeighborResponse(BaseModel):
    neighbors: List[Union[int, str]]

@functools.lru_cache
def load_model(community: AvailableCommunities):
    """
    Loads the recommendation model for a specific community.

    Parameters:
    - community (AvailableCommunities): The enumeration value representing the name of the community.

    Returns:
    - tuple: Model, CSR matrix.
    """
    # Define paths based on community name
    model_path = f"communities/{community.replace(' ', '-').lower()}/ease.pkl"
    im_path = f"communities/{community.replace(' ', '-').lower()}/im_csr.npz"

    # Check if files exist
    if not all(os.path.exists(path) for path in [model_path, im_path]):
        raise FileNotFoundError("One or more required files do not exist.")

    try:
        # Load model and data
        model = pickle.load(open(model_path, "rb"))
        im = load_npz(im_path)
    except Exception as e:
        raise IOError(f"An error occurred while reading the files: {e}")

    return model, im

@app.get(
    "/crps-rec/recommendations/{community}/{user_id}",
    response_model=RecommendationResponse,
    responses=RECOMMENDATION_RESPONSES
)
@app.get("/crps-rec/recommendations/{community}/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    community: AvailableCommunities,
    user_id: str = Path(
        ...,
        examples={
            "zbmath": {
                "summary": "zbMATH",
                "value": "eleftherakis.george-k",
            },
            "transport-research": {
                "summary": "Transport Research",
                "value": "0000-0002-9632-5947",
            },
            "digital-humanities-and-cultural-heritage": {
                "summary": "Digital Humanities and Cultural Heritage",
                "value": "0000-0002-7033-7798",
            },
            "energy-research": {
                "summary": "Energy Research",
                "value": "0000-0002-3704-4379",
            }
        }
    ),
    num_recs: int = Query(default=10, title="Number of Recommendations")
):
    """
    Generates recommendations for a user within a specific community.

    Parameters:
    - community: The enumeration value representing the name of the community.
    - user_id: The real user ID as stored in the database (ORCID or zbMATH author ID for zbMATH community).
    - num_recs: Number of recommendations to generate. Defaults to 10.

    Returns:
    - A dictionary containing the recommended item IDs.
    """
    try:
        db_name = "zbmath" if community == "zbMATH" else "fc4eosc"
        model, im = load_model(community)
        inner_user_id = get_inner_user_id(db_name, db_host, db_user, db_pass, db_port, community, user_id)

        logging.info(f"Internal user ID for {user_id} in {community}: {inner_user_id}")

        if inner_user_id is None:
            raise HTTPException(status_code=404, detail=f"No user found with user_id: {user_id}")

        user_interactions = im[int(inner_user_id), :].toarray()[0]
        recommended_item_ids = model.get_recommendations(user_interactions, n=num_recs)

        recommended_item_ids = get_real_item_id(db_name, db_host, db_user, db_pass, db_port, community, recommended_item_ids)

        return {"recommendations": recommended_item_ids}

    except Exception as e:
        logging.error(f"Error in get_recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/crps-rec/neighbors/{community}/{item_id}",
    response_model=NeighborResponse,
    responses=NEIGHBOR_RESPONSES
)
@app.get("/crps-rec/neighbors/{community}/{item_id}")
async def get_neighbors(
    community: AvailableCommunities,
    item_id: str = Path(
        ..., 
        examples={
            "zbmath": {
                "summary": "zbMATH",
                "value": "6317847",
            },
            "transport-research": {
                "summary": "Transport Research",
                "value": "50|doi_________::c15ed2c7d2ca9a24322114ba49a17bc2",
            },
            "digital-humanities-and-cultural-heritage": {
                "summary": "Digital Humanities and Cultural Heritage",
                "value": "50|doi_________::65224ede3e4a6458824babc5df48ed53",
            },
            "energy-research": {
                "summary": "Energy Research",
                "value": "50|doi_________::172b254de5141fd4689e673a5904c463",
            }
        }
    ),
    num_neighbors: int = Query(10, alias="num_neighbors", title="Number of Neighbors", description="Number of similar items to return.")
):
    """
    Finds items similar to a given item within a specific community.

    Parameters:
    - community: The enumeration value representing the name of the community.
    - item_id: The real item ID as stored in the database (result ID or zbMATH ID for zbMATH community).
    - num_neighbors: Number of similar items to return. Defaults to 10.

    Returns:
    - A dictionary containing the similar item IDs.
    """
    try:
        db_name = "zbmath" if community == "zbMATH" else "fc4eosc"
        model, _ = load_model(community)
        if community == "zbMATH": item_id = int(item_id)
        inner_item_ids = get_inner_item_id(db_name, db_host, db_user, db_pass, db_port, community, [item_id])

        logging.info(f"Internal item ID for {item_id} in {community}: {inner_item_ids[0]}")

        if not inner_item_ids:
            raise HTTPException(status_code=404, detail=f"No item found with item_id: {item_id}")

        neighbor_indices = model.get_neighbors(inner_item_ids[0], n=num_neighbors)

        # Convert internal neighbor IDs back to real item IDs
        neighbor_item_ids = get_real_item_id(db_name, db_host, db_user, db_pass, db_port, community, neighbor_indices)

        return {"neighbors": neighbor_item_ids}
    
    except Exception as e:
        logging.error(f"Error in get_neighbors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")