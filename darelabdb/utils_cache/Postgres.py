import json
from typing import Any, Dict, List, Optional, Union

from darelabdb.utils_database_connector.core import Database
from loguru import logger


class PostgresCache:
    """
    The PostgresCache will not inherit from CacheABC since its usage will be limited (storing and retrieving
    similarities of the Approximate similarity recommender). In the future it could be expanded.
    """

    def __init__(self, db_name: str, specific_schema: str = None):
        self.db = Database(db_name, specific_schema=specific_schema)

    def _initialize_table_if_not_exists(self, table_name):
        self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id TEXT PRIMARY KEY,
                data JSON
            );
            """,
            is_read=False,
            limit=-1,
        )

    def set_json(self, key: str, index: str, data: Union[List, Dict]) -> None:
        self._initialize_table_if_not_exists(key)
        query = f"""
            INSERT INTO {key}
            (id, data)
            VALUES (:id, :data);
        """

        # Execute insertion
        result = self.db.executemany(
            sql=query, data=[{"id": index, "data": json.dumps(data)}]
        )

        if "error" in result:
            logger.error(f"Failed to insert json: {result['error']}")

    def set_jsons(
        self, key: str, indexes: List[str], data: List[Union[List, Dict]]
    ) -> None:
        self._initialize_table_if_not_exists(key)
        query = f"""
            INSERT INTO {key}
            (id, data)
            VALUES (:id, :data);
        """

        self.db.executemany(
            sql=query,
            data=(
                list(
                    {"id": ind, "data": json.dumps(single_data)}
                    for ind, single_data in zip(indexes, data)
                )
            ),
        )

    def get_json(self, key: str, index: str) -> Optional[Union[List, Dict]]:
        res = self.db.execute(
            f"""
            SELECT data
            FROM {key}
            WHERE id = '{index}';
            """,
            limit=1,
        )

        if len(res) != 0:
            return res["data"][0]
        else:
            return None

    @staticmethod
    def export_to_file(file_path: str):
        """
        No file is created programmatically in the case of postgres. Instead, the psql command must be used
        if needed.
        """
        return None


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    pg = PostgresCache(db_name="fc4eosc", specific_schema="recsys_schema")
    pg.get_json(
        "metadata_similarities_faircore_similarity_based_rs",
        "doi_________::730603d4bd7157d673f75e0ffb9e39ed",
    )
