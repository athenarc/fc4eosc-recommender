
# Personalized Recommendations for Authors in Research Communities of the RDGraph

This project, developed by the DARElab team at the ATHENA Research Center, is part of the [FAIRCORE4EOSC European project](https://faircore4eosc.eu). Our goal is to enhance the discovery of research within the RDGraph by providing personalized recommendations to authors across different research communities. 

## Methodology 
The RDGraph organizes research products into distinct communities (subgraphs), each representing a unique research field. Our approach centers on analyzing citation edges within the RDGraph to discover relationships between authors. We extract these edges to construct an author-paper interaction matrix for each research community. This matrix is then processed using a collaborative filtering recommender system, which generates personalized recommendations for authors within each community.

## Database

[TODO]

## Components Overview

This section details the essential elements of this repository, each integral to the functionality and operation of our recommendation system:

- **database/rec_data.sql**: This SQL script configures the PostgreSQL schema for the recommender system. It establishes the database foundation necessary for processing and generating personalized recommendations by performing key operations:
  - **Creates a new schema** named `recsys_schema` and **defines an ENUM type** for interaction types (`authorship` and `cited`) that categorizes the nature of interactions within the database. 
  - **Creates and populates the interactions table** for tracking author-product interactions by community, using ORCID identifiers, product identifiers, and linked foreign keys to the main tables.
  - **Optimizes query performance** through materialized views and indices. This includes materialized views to summarize interaction frequencies and a table to store and rank recommendations for authors.
  - **Creates triggers and functions** to automate the filling of the recommendations table with bibliographic details.

- **database/rec_data.py**: This Python script provides the functionality needed to interact with the the database schema defined in `rec_data.sql`. It supports data retrieval, processing, and insertion for generating personalized recommendations. It contains several key functions:
  - **`get_citations_by_community`** and **`get_authorships_by_community`**: Retrieve citation and authorship interactions from the database for a specific community, returning a DataFrame with relevant data.
  - **`prepare_recommendation_data`**: Prepares data tuples for database insertion, organizing author IDs and recommended result IDs with corresponding ranks and community acronyms.
  - **`write_recommendations`**: Inserts recommendation records into the database based on prepared data tuples.
  - **`get_recommendations_by_author`**: Fetches and returns detailed recommendations for a specific author, including titles, types, publication dates, and publishers, organized by community and rank.

- **recommenders**: Contains the recommendation algorithms to be tested.

- **train.ipynb**: A Jupyter notebook for training the recommender system across different research communities, leveraging the data extracted from the RDGraph. *Note that we currently use only interactions of the type `cited` to train a recommender.*

- **communities**: This directory contains subfolders for each research community. Each subfolder contains the results of optimizing the recommender and the final results with the optimal parameters in json files.

- **main.py**: Serves as the entry point for the application, managing API interactions with the database that stores the recommendations.

## Execution Steps

Follow these steps to set up and run the recommendation system:

1. **Initialize the Database Schema**
   - Run the SQL file **`database/rec_data.sql`** to setup the `recsys_schema`. This step creates the necessary database structures like tables, views, and functions for the recommender system. It also populates the database with data on author-product interactions across various research communities, which will be used to train the recommendation algorithms.

2. **Train the Recommender System**
   - Open and run the Jupyter notebook **`train.ipynb`** to train the recommender system. Each community has a dedicated model that is trained with its respective data.
