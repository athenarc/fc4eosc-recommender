from typing import Any, Dict, List, Optional, Union

from pymongo import MongoClient


def form_mongo_url(username, password, host, port, auth_source) -> str:
    uri = f"mongodb://{username}:{password}@" if username and password else ""
    uri += f"{host}:{port}"
    uri += f"?authSource={auth_source}"
    return uri


class MongoCache:
    """
    The MongoCache will not inherit from CacheABC since its usage will be limited (storing and retrieving similarities
    of the Approximate similarity recommender). In the future it could be expanded.
    """

    def __init__(
        self,
        host: str,
        port: int,
        db_name: str,
        username: str = None,
        password: Any = None,
        auth_source: str = "admin",
    ):
        self._uri = form_mongo_url(username, password, host, port, auth_source)
        self._conn = None
        self._db_name = db_name
        self._db = None

    def get_db(self):
        return self._db

    def get_conn(self):
        return self._conn

    def connect(self):
        self._conn = MongoClient(self._uri)
        self._db = self._conn[self._db_name]

    def set_json(self, key: str, index: str, data: Union[List, Dict]) -> None:
        if self._db is None:
            self.connect()
        self._db[key].insert_one({"id": index, "data": data})

    def set_jsons(
        self, key: str, indexes: List[str], data: List[Union[List, Dict]]
    ) -> None:
        if self._db is None:
            self.connect()
        self._db[key].insert_many(
            (
                {"id": ind, "data": single_data}
                for ind, single_data in zip(indexes, data)
            )
        )

    def get_json(self, key: str, index: str) -> Optional[Union[List, Dict]]:
        if self._db is None:
            self.connect()
        data = self._db[key].find_one(
            {
                "id": index,
            }
        )

        if data is not None:
            return data["data"]
        else:
            return None

    @staticmethod
    def export_to_file(file_path: str):
        """
        No file is created programmatically in the case of mongo. Instead, the mongodump cli command must be used.
        """
        return None


if __name__ == "__main__":
    mongo = MongoCache(
        host="localhost",
        port=27017,
        db_name="similarity_recs",
        username="dev",
        password="dev",
    )
    mongo.connect()
    mongo.set_jsons(
        "similarities_test", indexes=["0", "1"], data=[{"aa": 11}, {"aa": 22}]
    )
