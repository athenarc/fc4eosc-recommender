from abc import ABC, abstractmethod
from typing import List, Optional, Union

import numpy as np
import pandas as pd

from darelabdb.utils_schemas.item import item_id_type


class SimilarityManager(ABC):
    cache_key: str
    indexes_cache_key: str

    # boolean (0 or 1) that checks if the similarities exist in redis. Will NOT catch if someone manually deletes the
    # similarities without deleting the flag
    exist_cache_key: str

    @abstractmethod
    def is_initialised(self) -> bool:
        """
        Checks if the similarities already exist.
        Returns:
            True if the similarities exist, False otherwise.
        """
        pass

    @abstractmethod
    def initialise(self, embeddings: Optional[pd.DataFrame] = None, **kwargs) -> None:
        """
        Checks if the similarities already exist.
        If not it creates and stores the similarities between given items.
        Args:
            embeddings (List[Item]): A list of items from which the embeddings will be created. If none it means that the
                                embeddings already exist in cache.
        """
        pass

    @abstractmethod
    def update(self, embeddings: pd.DataFrame, **kwargs) -> None:
        """
        Creates and stores the pairwise cosine similarity for the given embeddings.
        Args:
            embeddings (DataFrame): A dataframe with the ids and the embeddings of items.
        """
        pass

    @abstractmethod
    def get_similarities(self, items_ids: List[item_id_type]) -> pd.DataFrame:
        """
        Returns (pd.DataFrame): The similarities of an item with other items. The similarities are
        returned in the order that the ids were given.
        """
        pass
