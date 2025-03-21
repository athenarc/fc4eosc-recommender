from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd
from pandas import DataFrame


class Cache(ABC):
    dump_encoding = "base64"

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: The key to check

        Returns:
            (bool): True if key exists, False otherwise
        """
        pass

    @abstractmethod
    def set(self, key: str, data: Any) -> bool:
        """
        Sets the value of a key in the cache. The data can be of any type.

        Args:
            key: The key to set (or update)
            data: The value to set

        Returns:
            (bool): True if the key was set, False otherwise
        """
        pass

    @abstractmethod
    def get(self, key: str) -> Any:
        """
        Gets the value of a key in the cache. The data returned can be of any type.
        Args:
            key: The key to get

        Returns:
            (Any): The value of the key
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Deletes a key from the cache.
        Args:
            key: The key to delete

        """
        pass

    @abstractmethod
    def exists_df(self, key: str) -> bool:
        """
        Checks if a specific DataFrame exists in the cache.

        In most caches same as `exists(key)`, but some caches may have special handling for
        DataFrames.

        Args:
            key: The key of the DataFrame to check

        Returns:
            (bool): True if the DataFrame exists, False otherwise
        """
        pass

    @abstractmethod
    def set_df(self, key: str, data: DataFrame) -> bool:
        """
        Sets the value of a DataFrame in the cache.

        In most caches same as `set(key, data)`, but some caches may have special handling for DataFrames.

        Args:
            key: The key of the DataFrame to set
            data: The DataFrame to set

        Returns:
            (bool): True if the DataFrame was set, False otherwise
        """
        pass

    @abstractmethod
    def get_df(self, key: str) -> pd.DataFrame:
        """
        Gets the value of a DataFrame in the cache.

        In most caches same as `get(key)`, but some caches may have special handling for DataFrames.

        Args:
            key: The key of the DataFrame to get

        Returns:
            (pd.DataFrame): The DataFrame returned
        """
        pass

    @abstractmethod
    def delete_df(self, key: str) -> None:
        """
        Deletes a DataFrame from the cache.

        In most caches same as `delete(key)`, but some caches may have special handling for DataFrames.

        Args:
            key: The key of the DataFrame to delete

        """
        pass

    @abstractmethod
    def exists_vector(self, key: str, index: str) -> bool:
        """
        Checks if a specific vector exists in the cache under a specific index.

        The same as `exists(f"{key}:{index}")`, but some caches may have special handling for vectors.

        Args:
            key: The key of the vector to check
            index: The index of the vector to check

        Returns:
            (bool): True if the vector exists, False otherwise
        """
        pass

    @abstractmethod
    def set_vector(self, key: str, index: str, data: np.array) -> bool:
        """
        Sets the value of a vector (`np.array`) in the cache under a specific index.

        Args:
            key: The key of the vector to set
            index: The index of the vector to set
            data: The vector to set in `np.array` format

        Returns:
            (bool): True if the vector was set, False otherwise
        """
        pass

    @abstractmethod
    def set_vectors(self, data: List[tuple[str, str, np.array]]) -> bool:
        """
        Sets the value of multiple vectors (`np.array`) in the cache under a specific key and index.

        **Example input**

        ```python
        [
            ("key1", "index1", np.array([1,2,3])),
            ("key1", "index2", np.array([4,5,6])),
            ("key2", "index1", np.array([7,8,9])),
        ]
        ```

        Args:
            data: A list of tuples containing the key, index and vector to set

        Returns:
            (bool): True if the vectors were set, False otherwise
        """
        pass

    @abstractmethod
    def get_vector(self, key: str, index: str) -> np.array:
        """
        Gets the value of a vector (`np.array`) in the cache under a specific index.

        Args:
            key: The key of the vector to get
            index: The index of the vector to get

        Returns:
            (np.array): The vector returned
        """
        pass

    @abstractmethod
    def get_vectors(self, key: str, indexes: List[str]) -> List[np.array]:
        """
        Gets the value of multiple vectors (`np.array`) in the cache under a specific key given the indexes.

        Args:
            key: The key that the vectors are under
            indexes: The index values of the vectors to get

        Returns:
            (List[np.array]): The vectors returned
        """
        pass

    @abstractmethod
    def delete_vector(self, key: str, index: str) -> None:
        """
        Deletes a vector from the cache under a specific key and index.

        Args:
            key: The key of the vector to delete
            index: The index of the vector to delete

        """
        pass

    @abstractmethod
    def get_json(self, key: str, index: str) -> Union[List, Dict]:
        """
        Gets the value of a json object in the cache under a specific index. This method also covers the transformation
        from json string to python object (`dict` or `list).

        Args:
            key: The key of the json object to get
            index: The index of the json object to get

        Returns:
            (Union[List, Dict]): The json object returned as a python object

        """
        pass

    @abstractmethod
    def set_json(self, key: str, index: str, data: Union[List, Dict]) -> None:
        """
        Sets the value of a json object in the cache under a specific index. This method also covers the transformation
        from python object (`dict` or `list`) to json string.

        **Example usage**
        ```python
        cache.set_json("key", "index", {"a": 1, "b": 2})
        cache.set_json("key", "index", [1, 2, {3: "a"}])
        ```

        Args:
            key: The key of the json object to set
            index: The index of the json object to set
            data: The python object to set as a json string

        """
        pass

    @abstractmethod
    def delete_on_prefix(self, prefix: str) -> None:
        """
        Deletes all keys with a specific prefix.

        Example call `cache.delete_on_prefix("prefix:")` will delete all keys starting with "prefix:".

        Args:
            prefix: The prefix to delete

        """
        pass

    @abstractmethod
    def export_to_file(self, path: str) -> None:
        """
        Exports the cache to a JSON file. Everything in the output will be <self.dump_encoding> encoded.

        Args:
            path: The path to the output JSON file
        """
        pass

    @abstractmethod
    def import_from_file(self, path: str) -> None:
        """
        Imports from a JSON file.

        Args:
            path: The path to the input JSON file
        """
        pass
