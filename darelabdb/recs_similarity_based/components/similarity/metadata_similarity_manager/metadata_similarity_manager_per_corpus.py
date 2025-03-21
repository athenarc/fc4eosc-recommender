from typing import List, Optional, Union

import numpy as np
import pandas as pd
from darelabdb.recs_similarity_based.components.similarity.SimilarityManagerABC import (
    SimilarityManager,
)
from darelabdb.utils_cache.CacheABC import Cache
from loguru import logger
from sklearn.metrics.pairwise import cosine_similarity

from darelabdb.utils_schemas.item import item_id_type


class MetadataSimilarityManagerPerCorpus(SimilarityManager):
    """
    The MetadataSimilarityManagerPerCorpus class is responsible for the creation and caching of the items' metadata
    similarity. For each item the similarity manager will store the pairwise similarities with all the corpus items.
    """

    cache_key = "metadata_similarities"
    indexes_cache_key = "metadata_similarities_indexes"
    exist_cache_key = "metadata_similarities_exists"

    def __init__(self, cache_manager: Cache, recommender_id: str = None) -> None:
        """
        Args:
            cache_manager (Cache): The cache model in which the embeddings will be stored.
            recommender_id (str): The id of the recommender that will be used to create the cache key.
        """
        if recommender_id is not None:
            self.cache_key = f"{self.cache_key}_{recommender_id}"
            self.indexes_cache_key = f"{self.indexes_cache_key}_{recommender_id}"
            self.exist_cache_key = f"{self.exist_cache_key}_{recommender_id}"
        self.cache_manager = cache_manager

    def is_initialised(self) -> bool:
        """
        Checks if the metadata similarities already exist.
        Returns:
            True if the metadata similarities exist, False otherwise.
        """
        return (
            self.cache_manager.exists(self.exist_cache_key)
            and self.cache_manager.get(self.exist_cache_key) == 1
        )

    def initialise(self, embeddings: Optional[pd.DataFrame] = None) -> None:
        """
        Checks if the metadata similarities already exist.
        If not it creates and stores the similarities between given items.

        Args:
            embeddings (List[Item]): A list of items from which the embeddings will be created. If none it means that the
                                embeddings already exist in cache.
        """
        if not self.is_initialised() and embeddings is not None:
            self.update(embeddings)
        elif not self.is_initialised() and embeddings is None:
            logger.error(f"{self.cache_key} do not exist in cache, cannot initialize.")
            raise KeyError(
                f"{self.cache_key} do not exist. Possible solution: Run the `update` method "
                "of the recommender and provide the list of your items."
            )
        else:
            logger.info(f"Using the {self.cache_key} in cache.")

    def update(self, embeddings: pd.DataFrame) -> None:
        """
        Creates and stores the pairwise cosine metadata similarity for the given embeddings.
        Args:
            embeddings (DataFrame): A dataframe with the ids and the embeddings of items.
        """

        logger.info(f"Creating the {self.cache_key}...")

        similarities = [
            (self.cache_key, str(item_index), item_similarities)
            for item_index, item_similarities in zip(
                embeddings.index, cosine_similarity(embeddings.to_numpy())
            )
        ]

        # Store similarities
        self.cache_manager.set_json(
            key=self.indexes_cache_key, index="", data=list(embeddings.index)
        )
        self.cache_manager.set_vectors(similarities)

        self.cache_manager.set(self.exist_cache_key, 1)

    def get_similarities(self, items_ids: List[item_id_type]) -> pd.DataFrame:
        """
        Returns (pd.DataFrame): The similarities of an item with the corpus of items.

        !!! The current version of the method does not support multiple items in the items_ids list!

        For example if items_ids = [1, 2] and the ids of the items in the corpus are [1, 2, 3, 4, 5] the returned
        dataframe would look like
                     1     2     3     4    5
                1  0.5 | 0.3 | 0.2 | 0.4 | 0.8
                2  0.2 | 0.6 | 0.1 | 0.7 | 0.3
        """
        # Get the indexes of the items
        indexes = self.cache_manager.get_json(key=self.indexes_cache_key, index="")

        # Get the similarities for all items in items_ids
        vectors = self.cache_manager.get_vectors(
            self.cache_key, [str(item_id) for item_id in items_ids]
        )

        similarities = pd.DataFrame(
            data=np.array(vectors), index=items_ids, columns=indexes
        )

        return similarities
