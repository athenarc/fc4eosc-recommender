
import psycopg2
import pandas as pd

# Get all interactions of type "cited" for a given community
def get_interactions_by_community(db_name, db_host, db_user, db_pass, db_port, community_name):
    sql_query = """
    SELECT author_id, result_id, interaction_count
    FROM recsys_schema.interactions_mview
    WHERE community_name = %s AND interaction_type = 'cited';
    """

    try:
        with psycopg2.connect(
            dbname=db_name, 
            host=db_host, 
            user=db_user, 
            password=db_pass, 
            port=db_port
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, (community_name,))
                result = cur.fetchall()
                df = pd.DataFrame(result, columns=["author_id", "result_id", "interaction_count"])

        return df

    except Exception as e:
        print("Error: ", e)
        return None
    
def write_users_mappings(db_name, db_host, db_user, db_pass, db_port, data):
    sql_insert_query = """
    INSERT INTO recsys_schema.users_mappings (inner_id, author_id, community_name)
    VALUES (%s, %s, %s);
    """

    try:
        with psycopg2.connect(
            dbname=db_name,
            host=db_host,
            user=db_user,
            password=db_pass,
            port=db_port
        ) as conn:
            with conn.cursor() as cur:
                cur.executemany(sql_insert_query, data)
                conn.commit()

        print("Data inserted successfully into users_mappings.")

    except Exception as e:
        print("Error: ", e)

def write_items_mappings(db_name, db_host, db_user, db_pass, db_port, data):
    sql_insert_query = """
    INSERT INTO recsys_schema.items_mappings (inner_id, result_id, community_name)
    VALUES (%s, %s, %s);
    """

    try:
        with psycopg2.connect(
            dbname=db_name,
            host=db_host,
            user=db_user,
            password=db_pass,
            port=db_port
        ) as conn:
            with conn.cursor() as cur:
                cur.executemany(sql_insert_query, data)
                conn.commit()

        print("Data inserted successfully into items_mappings.")

    except Exception as e:
        print("Error: ", e)

def get_user_mapping(db_name, db_host, db_user, db_pass, db_port, community_name, author_id):
    """
    Fetches the internal user ID for a given community and author_id from the database.
    """
    sql_query = """
    SELECT inner_id FROM recsys_schema.users_mappings
    WHERE author_id = %s AND community_name = %s;
    """

    try:
        with psycopg2.connect(
            dbname=db_name, 
            host=db_host, 
            user=db_user, 
            password=db_pass, 
            port=db_port
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, (author_id, community_name))
                result = cur.fetchone()
                if result:
                    return result[0]
                else:
                    return None

    except Exception as e:
        print("Error in get_user_mapping: ", e)
        return None
    
def get_item_mapping(db_name, db_host, db_user, db_pass, db_port, community_name, internal_item_ids):
    """
    Fetches the real item IDs for a given community based on internal item indices from the database.
    """
    sql_query = """
    SELECT result_id FROM recsys_schema.items_mappings
    WHERE inner_id = ANY(%s) AND community_name = %s;
    """

    try:
        with psycopg2.connect(
            dbname=db_name, 
            host=db_host, 
            user=db_user, 
            password=db_pass, 
            port=db_port
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, (internal_item_ids, community_name))
                result = cur.fetchall()
                return [item[0] for item in result]

    except Exception as e:
        print("Error in get_item_mapping: ", e)
        return None