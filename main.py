# Standard imports
import os
import functools
from typing import Union
from urllib.parse import unquote
from enum import Enum

# Third-party imports
from fastapi import FastAPI, Query, HTTPException
import pickle
import pandas as pd
from scipy.sparse import load_npz

app = FastAPI(
    openapi_url= "/crps-rec/openapi.json",
    docs_url="/crps-rec/docs",
    redoc_url= "/crps-rec/redoc",
)

class AvailableCommunities(str, Enum):
    zbmath = "zbmath"
    dariah = "dariah"
    humanities = "digital-humanities"
    transport = "transport-research"

@functools.lru_cache
def load_model(community: AvailableCommunities):
    """
    Loads the recommendation model and mappings for a specific community.

    Parameters:
    - community (AvailableCommunities): The enumeration value representing the name of the community.

    Returns:
    - tuple: Model, CSR matrix, Items mapping, Users mapping.
    """

    # Define paths based on community name
    model_path = f"communities/{community}/ease.pkl"
    csr_path = f"communities/{community}/csr.npz"
    items_mapping_path = f"communities/{community}/items_mapping.parquet"
    users_mapping_path = f"communities/{community}/users_mapping.parquet"

    # Check if files exist
    if not all(os.path.exists(path) for path in [model_path, csr_path, items_mapping_path, users_mapping_path]):
        raise FileNotFoundError("One or more required files do not exist.")

    try:
        # Load model and data
        model = pickle.load(open(model_path, "rb"))
        csr = load_npz(csr_path)
        items_mapping = pd.read_parquet(items_mapping_path)
        users_mapping = pd.read_parquet(users_mapping_path)
    except Exception as e:
        raise IOError(f"An error occurred while reading the files: {e}")

    return model, csr, items_mapping, users_mapping

@app.get("/crps-rec/recommendations/{community}")
async def get_recommendations(community: AvailableCommunities, user_id: str, num_recs: int = Query(10, alias="num-recommendations")):
    """
    Generates recommendations for a user within a specific community.

    Parameters:
    - community (AvailableCommunities): The enumeration value representing the name of the community.
    - user_id (str): The real user ID as stored in the database.
    - num_recs (int, optional): Number of recommendations to generate. Defaults to 10.

    Returns:
    - dict: A dictionary containing the recommended item IDs.

    Example Request:
    ```bash
    curl -X 'GET' 'https://test.darelab.athenarc.gr/crps-rec/recommendations/zbmath?user_id=bracic.janko'
    curl -X 'GET' 'https://test.darelab.athenarc.gr/crps-rec/recommendations/dariah?user_id=0000-0001-5086-7284'
    ```
    """

    model, csr, items_mapping, users_mapping = load_model(community)
    
    # Query to find internal user ID corresponding to the real user ID
    query_result = users_mapping.query(f"user_id == '{user_id}'")["uid"].values
    
    if query_result.size == 0:
        raise HTTPException(status_code=404, detail=f"No user found with user_id: {user_id}")
    
    internal_user_id = query_result[0]
    
    # Retrieve user interactions from CSR matrix
    user_interactions = csr[internal_user_id,:].toarray()[0]
    
    recommended_indices = model.get_recommendations(user_interactions, n=num_recs)
    
    # Map internal item IDs to real item IDs
    recommended_item_ids = items_mapping.loc[recommended_indices, "item_id"].values.tolist()
    
    return {"recommendations": recommended_item_ids}

@app.get("/crps-rec/neighbors/{community}/{item_id}")
async def get_neighbors(community: AvailableCommunities, item_id: str, num_neighbors: int = Query(10, alias="num_neighbors")):
    """
    Finds items similar to a given item within a specific community.

    Parameters:
    - community (AvailableCommunities): The enumeration value representing the name of the community.
    - item_id (int): The ID of the item as stored in the database.
    - num_neighbors (int, optional): Number of similar items to return. Defaults to 10.

    Returns:
    - dict: A dictionary containing the similar item IDs.

    Example Request:
    ```bash
    curl -X 'GET' 'https://test.darelab.athenarc.gr/crps-rec/neighbors/zbmath/62169'
    curl -X 'GET' 'https://test.darelab.athenarc.gr/crps-rec/neighbors/dariah/50|doi_dedup___::58dd5e1434928c01d76277563e193820'
    ```
    """
    model, _, items_mapping, _ = load_model(community)

    # Decode based on community
    decoded_item_id = unquote(item_id) if community.lower() != "zbmath" else int(item_id)

    # Perform the query depending on the type
    if isinstance(decoded_item_id, int):
        query_result = items_mapping.query(f"item_id == {decoded_item_id}")["iid"].values
    else:
        query_result = items_mapping.query(f"item_id == '{decoded_item_id}'")["iid"].values

    if query_result.size == 0:
        raise HTTPException(status_code=404, detail=f"No item found with item_id: {item_id}")

    internal_item_id = query_result[0]

    neighbor_indices = model.get_neighbors(internal_item_id, n=num_neighbors)

    # Map internal neighbor IDs to real item IDs
    neighbor_item_ids = items_mapping.loc[neighbor_indices, "item_id"].values.tolist()

    return {"neighbors": neighbor_item_ids}

# Run the app: uvicorn main:app --reload
# Replace https://test.darelab.athenarc.gr/ with http://127.0.0.1:8000/ to run locally
# http://127.0.0.1:8000/crps-rec/redoc
# http://127.0.0.1:8000/crps-rec/docs
