from typing import List
from darelabdb.utils_database_connector.core import Database
from loguru import logger

import pandas as pd

import json
    
# Get all interactions of type "cited" for a given community
def get_citations_by_community(query_executor: Database, community_acronym: str) -> pd.DataFrame:
    """
    Get all citation interactions for a specified community from the database.
    
    Parameters:
    - query_executor: Database connection object.
    - community_acronym: Acronym of the community to filter interactions.
    
    Returns:
    - DataFrame containing citation data including author ID, result ID, and interaction count.
    """
    sql_query = f"""
    SELECT author_id, result_id, interaction_count
    FROM recsys_schema.interactions_mview
    WHERE community_acronym = '{community_acronym}' AND interaction_type = 'cited';
    """
    try:
        result = query_executor.execute(sql_query, limit=0)
        df = pd.DataFrame(result, columns=["author_id", "result_id", "interaction_count"])
        return df
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
# Get all interactions of type "authorship" for a given community
def get_authorships_by_community(query_executor: Database, community_acronym: str) -> pd.DataFrame:
    """
    Get all authorship interactions for a specified community from the database.
    
    Parameters:
    - query_executor: Database connection object.
    - community_acronym: Acronym of the community to filter interactions.
    
    Returns:
    - DataFrame containing authorship data including author ID, result ID, and interaction count.
    """
    sql_query = f"""
    SELECT author_id, result_id, interaction_count
    FROM recsys_schema.interactions_mview
    WHERE community_acronym = '{community_acronym}' AND interaction_type = 'authorship';
    """
    try:
        result = query_executor.execute(sql_query, limit=0)
        df = pd.DataFrame(result, columns=["author_id", "result_id", "interaction_count"])
        return df
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
def prepare_recommendation_data(author_ids, recommendations, community_acronym):
    """
    Prepare data tuples for database insertion.
    
    Parameters:
    - author_ids: List of author IDs.
    - recommendations: List of recommended result IDs for each author.
    - community_acronym: Community acronym applicable to all recommendations.
    
    Returns:
    - List of dictionaries for insertion into the database.
    """
    data_tuples = []
    for author_id, recs in zip(author_ids, recommendations):
        for rank, result_id in enumerate(recs, start=1):
            data_tuples.append({
                'author_id': str(author_id),
                'result_id': str(result_id),
                'rank': int(rank),
                'community_acronym': str(community_acronym)
            })
    return data_tuples
    
def write_recommendations(query_executor: Database, data_tuples):
    """
    Writes recommendation records to the database.

    Parameters:
    - query_executor: Database connection object.
    - data_tuples: List of dictionaries, each representing a record to be inserted into the database.
                   Each dictionary must contain the following keys:
                   - 'author_id': a string representing the author's ID
                   - 'result_id': a string representing the result's ID
                   - 'rank': an integer representing the rank of the recommendation
                   - 'community_acronym': a string representing the acronym of the community

    Example of data_tuples:
    [
        {
            'author_id': '0000-0003-4187-6044', 
            'result_id': '50|doi_dedup___::ad370695ee5a49210627747773b6b681', 
            'rank': 1, 
            'community_acronym': 'dh-ch'
        }
    ]

    Each dictionary corresponds to a single row to be inserted into the recsys_schema.recommendations table.
    """
    sql_query = """
    INSERT INTO recsys_schema.recommendations_new (author_id, result_id, rank, community_acronym)
    VALUES (:author_id, :result_id, :rank, :community_acronym);
    """
    try:
        result = query_executor.executemany(sql_query, data_tuples)
        if 'error' in result:
            raise Exception(result['error'])
        else:
            logger.info("Data inserted successfully into recommendations.")
    except Exception as e:
        logger.error(f"Error: {e}")

def get_recommendations_by_author(query_executor: Database, author_id: str) -> pd.DataFrame:
    """
    Get recommendations for a specific author grouped by community, including the title, type, publication date, and publisher, ordered by rank.

    Parameters:
    - query_executor: Database connection object.
    - author_id: ORCID identifier of the author to filter recommendations.

    Returns:
    - DataFrame containing recommendation data including community, title, type, publication date, and publisher.
    """
    sql_query = f"""
    SELECT 
        community_acronym, 
        result_id,
        result_title, 
        result_type,
        result_publication_date,
        result_publisher
    FROM 
        recsys_schema.recommendations_new 
    WHERE 
        author_id = '{author_id}' 
    ORDER BY 
        community_acronym, 
        rank;
    """
    try:
        logger.info(f"Executing SQL query for author_id {author_id}.")
        result = query_executor.execute(sql_query, limit=0)
        df = pd.DataFrame(result, columns=["community_acronym", "result_id", "result_title", "result_type", "result_publication_date", "result_publisher"])
        logger.info(f"Query returned {len(df)} records.")
        return df
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
def get_top_cited_by_community(query_executor: Database) -> pd.DataFrame:
    """
    Get the top 20 most cited publications per community.

    Parameters:
    - query_executor: Database connection object.

    Returns:
    - DataFrame containing top cited publications including community, result ID, title, type, 
      publication date, and publisher.
    """
    sql_query = """
    SELECT 
        community_acronym, 
        result_id,
        COALESCE(result_title, '') AS result_title, 
        COALESCE(result_type, '') AS result_type,
        result_publication_date,
        COALESCE(result_publisher, '') AS result_publisher
    FROM 
        recsys_schema.top20_cited_results
    ORDER BY 
        community_acronym, rank;
    """
    try:
        result = query_executor.execute(sql_query, limit=0)
        df = pd.DataFrame(result, columns=[
            "community_acronym", "result_id", "result_title", "result_type", 
            "result_publication_date", "result_publisher"
        ])
        return df
    except Exception as e:
        logger.error(f"Error fetching top cited publications: {e}")
        return None
    
def get_available_communities(query_executor: Database) -> List[str]:
    """
    Get the list of distinct available communities from the interactions materialized view.

    Parameters:
    - query_executor: Database connection object.

    Returns:
    - List of community acronyms as strings.
    """
    sql_query = """
    SELECT DISTINCT community_acronym
    FROM recsys_schema.interactions_mview;
    """
    try:
        result = query_executor.execute(sql_query, limit=0)
        
        # Convert the DataFrame column to a list
        df = pd.DataFrame(result, columns=["community_acronym"])
        return df["community_acronym"].tolist()

    except Exception as e:
        logger.error(f"Error fetching available communities: {e}")
        return []

if __name__ == "__main__":
    db = Database("fc4eosc")

    # print(get_citations_by_community(db, "dariah").head())
    # print(get_authorships_by_community(db, "dariah").head())

    # author_id = "0000-0003-1302-1049"
    # df = get_recommendations_by_author(db, author_id)
    # print(df)
    # # Group by community and convert to list of records
    # grouped = df.groupby('community_acronym').apply(lambda x: x.drop(columns=['community_acronym']).to_dict(orient='records')).to_dict()
    # # Convert to desired format
    # result_json = {community: records for community, records in grouped.items()}
    # json_str = json.dumps(result_json, indent=4)
    # print(json_str)

    # top_cited = get_top_cited_by_community(db)
    # print(top_cited)
    
    get_available_communities(db)
