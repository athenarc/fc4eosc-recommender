import codecs
import json
import pickle
import zlib
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd
import redis
from darelabdb.utils_cache.CacheABC import Cache
from pandas import DataFrame


class RedisCache(Cache):
    def __init__(self, host: str, port: int, password: Any = None):
        self.cache = redis.Redis(host=host, port=port, password=password)
        self.cache.ping()

    def exists(self, key: str) -> bool:
        return self.cache.exists(key)

    def set(self, key: str, data: Any) -> bool:
        return self.cache.set(key, data)

    def get(self, key: str) -> Any:
        if not self.cache.exists(key):
            raise KeyError()
        return self.cache.get(key)

    def delete(self, key: str) -> None:
        self.cache.delete(key)

    def exists_df(self, key: str) -> bool:
        return self.exists(key)

    def set_df(self, key: str, data: DataFrame) -> bool:
        """
        Creates an entry in redis to store the given dataframe.
        Args:
            key (str): The name of the entry in redis
            data (DataFrame): The structure stored in redis
        """
        data_compressed = zlib.compress(pickle.dumps(data))
        return self.set(key, data_compressed)

    def get_df(self, key: str) -> pd.DataFrame:
        data = self.get(key)
        return pickle.loads(zlib.decompress(data))

    def delete_df(self, key: str) -> None:
        self.delete(key)

    def exists_vector(self, key: str, index: str) -> bool:
        return self.exists(f"{key}" + (f":{index}" if len(index) else ""))

    def set_vector(self, key: str, index: str, data: np.array) -> bool:
        """
        Creates an entry <key:index> : <data>.
        Args:
            key (str): The name that describes the stored data.
            index (str): The identification of the value.
            data (np.array): The data stored in redis.
        """
        return self.set(
            f"{key}" + (f":{index}" if len(index) else ""),
            data.astype(np.float32).tobytes(),
        )

    def set_vectors(self, data: List[tuple[str, str, np.array]]):
        pipe = self.cache.pipeline()
        for key, index, vector in data:
            pipe.set(
                f"{key}" + (f":{index}" if len(index) else ""),
                vector.astype(np.float32).tobytes(),
            )
        pipe.execute()

    def get_vector(self, key: str, index: str) -> np.array:
        value_bytes = self.get(f"{key}" + (f":{index}" if len(index) else ""))
        return np.frombuffer(value_bytes, dtype=np.float32)

    def get_vectors(self, key: str, indexes: List[str]) -> List[np.array]:
        pipe = self.cache.pipeline()
        for index in indexes:
            pipe.get(f"{key}" + (f":{index}" if len(index) else ""))
        return [
            np.frombuffer(vector_bytes, dtype=np.float32)
            for vector_bytes in pipe.execute()
        ]

    def delete_vector(self, key: str, index: str) -> None:
        self.delete(f"{key}" + (f":{index}" if len(index) else ""))

    def get_json(self, key: str, index: str) -> Union[List, Dict]:
        return json.loads(self.get(f"{key}" + (f":{index}" if len(index) else "")))

    def set_json(self, key: str, index: str, data: Union[List, Dict]) -> None:
        self.set(f"{key}" + (f":{index}" if len(index) else ""), json.dumps(data))

    def delete_on_prefix(self, prefix: str) -> None:
        for key in self.cache.scan_iter(f"{prefix}*"):
            self.cache.delete(key)

    def export_to_file(self, path: str) -> None:
        exported = []
        cur = 0
        while True:
            cur, key_list = self.cache.scan(cur, match="*")
            for key in key_list:
                encoded_key = codecs.decode(codecs.encode(key, self.dump_encoding))
                encoded_value = codecs.decode(
                    codecs.encode(self.cache.dump(key), self.dump_encoding)
                )
                exported.append((encoded_key, encoded_value))
            if cur == 0:
                break

        with open(path, "w", encoding="utf-8") as fo:
            json.dump(exported, fo, ensure_ascii=True, indent=0)

    def import_from_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as fi:
            result = json.load(fi)
        pipe = self.cache.pipeline()
        for key, value in result:
            pipe.restore(
                codecs.decode(codecs.encode(key), self.dump_encoding),
                0,
                codecs.decode(codecs.encode(value), self.dump_encoding),
                replace=True,
            )
        pipe.execute()
