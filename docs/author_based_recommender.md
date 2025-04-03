
# Personalized Recommendations for Authors in Research Communities of the RDGraph

## Methodology 

The RDGraph organizes research products into distinct communities (subgraphs), each representing a unique research topic. Our approach centers on analyzing citation edges within the RDGraph to discover relationships between authors. We extract these edges to construct an author-paper interaction matrix for each research community. This matrix is then processed using a collaborative filtering recommender system, which generates personalized recommendations for authors within each community.

## API

The API docs of the recommender can be found:
[https://darelab.athenarc.gr/api/faircore/user-to-item-recommender/docs](https://darelab.athenarc.gr/api/faircore/user-to-item-recommender/docs)

## Components Overview

Below is an overview of the core components that support the recommender system:

- **`sql/build_recommenders_schema.sql`**:  
  Sets up the PostgreSQL schema for the recommender system. Key operations include:
  - Creating the `recsys_schema` and defining an ENUM type for interaction types (`authorship`, `cited`).
  - Creating and populating the interactions table with author-product interactions by community, using ORCID and product identifiers.
  - Optimizing query performance using materialized views and indices.
  - Creating triggers and functions to auto-populate the recommendations table with bibliographic details.

- **`darelabdb/api_faircore_neighborhood_learning_recs/db/rec_data.py`**:  
  Handles database interactions, including data retrieval, preparation, and insertion. Main functions:
  - `get_citations_by_community()` and `get_authorships_by_community()` – retrieve interaction data for a given community.
  - `prepare_recommendation_data()` – formats recommendation results for insertion.
  - `write_recommendations()` – writes generated recommendations to the database.
  - `get_recommendations_by_author()` – fetches recommendations for a specific author, returning titles, types, publication dates, and publishers by community and rank.

- **`darelabdb/recs_neighborhood_learning/`**:  
  Directory containing the implemented recommendation algorithms.
  *Currently, EASE recommender is used, known for its SOTA performance.*

- **`darelabdb/api_faircore_neighborhood_learning_recs/train.ipynb`**:  
  Jupyter notebook used to train recommenders for each community using RDGraph interaction data.  
  *Currently, only `cited` interactions are used for training.*

- **`darelabdb/api_faircore_neighborhood_learning_recs/communities/`**:  
  Contains subfolders for each research community. Each folder holds optimization results and final recommendation outputs in JSON format.

- **`darelabdb/api_faircore_neighborhood_learning_recs/api.py`**:  
  The application’s entry point. It manages API calls and handles interactions with the recommendations database.

## Execution Steps

Follow these steps to set up and run the recommendation system:

1. **Initialize the Database Schema**  
   - Run **`sql/build_recommenders_schema.sql`** to set up `recsys_schema`. This creates all necessary database tables, views, and functions, and populates the schema with interaction data across communities.

2. **Train the Recommender System**  
   - Open and run **`darelabdb/api_faircore_neighborhood_learning_recs/train.ipynb`** to train a recommendation model for each research community. The training uses community-specific citation data, and the resulting recommendations are stored in the database for fast and structured retrieval.
