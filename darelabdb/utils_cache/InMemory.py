import codecs
import json
import pickle
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd
from darelabdb.utils_cache.CacheABC import Cache
from pandas import DataFrame


class InMemoryCache(Cache):
    def __init__(self):
        self.cache = {}

    def exists(self, key: str) -> bool:
        return key in self.cache

    def set(self, key: str, data: Any) -> bool:
        self.cache[key] = data
        return True

    def get(self, key: str) -> Any:
        return self.cache[key]

    def delete(self, key: str) -> None:
        del self.cache[key]

    def exists_df(self, key: str) -> bool:
        return self.exists(key)

    def set_df(self, key: str, data: DataFrame) -> bool:
        return self.set(key, data)

    def get_df(self, key: str) -> pd.DataFrame:
        return self.get(key)

    def delete_df(self, key: str) -> None:
        self.delete(key)

    def exists_vector(self, key: str, index: str) -> bool:
        return self.exists(key=f"{key}:{index}")

    def set_vector(self, key: str, index: str, data: np.array) -> bool:
        return self.set(key=f"{key}" + (f":{index}" if len(index) else ""), data=data)

    def set_vectors(self, data: List[tuple[str, str, np.array]]) -> bool:
        for key, index, vector in data:
            self.set_vector(key, index, vector)
        return True

    def get_vector(self, key: str, index: str) -> np.array:
        return self.get(f"{key}" + (f":{index}" if len(index) else ""))

    def get_vectors(self, key: str, indexes: List[str]) -> List[np.array]:
        return [self.get_vector(key, index) for index in indexes]

    def delete_vector(self, key: str, index: str) -> None:
        self.delete(f"{key}" + (f":{index}" if len(index) else ""))

    def get_json(self, key: str, index: str) -> Union[List, Dict]:
        return json.loads(self.get(f"{key}" + (f":{index}" if len(index) else "")))

    def set_json(self, key: str, index: str, data: Union[List, Dict]) -> None:
        self.set(f"{key}" + (f":{index}" if len(index) else ""), json.dumps(data))

    def delete_on_prefix(self, prefix: str) -> None:
        deleted_keys = [key for key in self.cache.keys() if key.startswith(prefix)]
        for key in deleted_keys:
            self.delete(key)

    def export_to_file(self, path: str) -> None:
        exported = []
        for key, value in self.cache.items():
            # Then encoding goes bytes via pickle -> base64 via codecs -> str via codecs
            encoded_key = codecs.decode(
                codecs.encode(pickle.dumps(key), self.dump_encoding)
            )
            encoded_value = codecs.decode(
                codecs.encode(pickle.dumps(value), self.dump_encoding)
            )
            exported.append((encoded_key, encoded_value))

        with open(path, "w") as f:
            json.dump(exported, f, ensure_ascii=True, indent=0)

    def import_from_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            result = json.load(f)

        for key, value in result:
            # The decoding goes str via codecs -> bytes via codecs -> python object via pickle
            decoded_key = pickle.loads(
                codecs.decode(codecs.encode(key), self.dump_encoding)
            )
            decoded_value = pickle.loads(
                codecs.decode(codecs.encode(value), self.dump_encoding)
            )

            self.set(decoded_key, decoded_value)
