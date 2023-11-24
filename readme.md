
# Personalized Recommendations for Authors in Research Communities

## Overview
This project, developed by the DARElab team at ATHENA Research Center for the FAIRCORE4EOSC European project, focuses on building recommendation engines tailored for authors across various research communities. 
Our goal is to assist researchers in discovering the papers they need. To achieve this, we are looking at the connections in the RDGraph. We focus on two important kinds of connections: the ones that show who wrote which papers (authorship edges) and the ones that show which papers cite others (cited edges). 
By using these links, we want to make it simpler for researchers to find important and relevant papers in their field. Our project is all about making research easier to navigate and more connected for those who are contributing to it.

## Project Structure

### Main Components
- **main.py**: Entry point for the application. Handles API calls to the recommender system.
- **database/rec_data.sql**: Includes SQL commands for setting up the schema of the recommender in a PostgreSQL database.
- **notebooks/train.ipynb**: A Jupyter notebook for training the recommender system across different research communities, leveraging data extracted from the RDGraph.

### Specialized Directories
- **communities**: This directory contains subfolders for each research community. Each subfolder is equipped with:
  - A sparse matrix (authors x research products) representing citation frequencies of papers by specific authors.
  - Two JSON files: one detailing the results of the trained recommender, and another listing parameters used to derive the optimal recommender settings.
- **src**: Encompasses three subdirectories:
  - **api**: For API related functionalities.
  - **helpers**: Utility scripts and functions aiding various operations of the system.
  - **recommenders**: Contains the algorithms of the recommender systems deployed.
