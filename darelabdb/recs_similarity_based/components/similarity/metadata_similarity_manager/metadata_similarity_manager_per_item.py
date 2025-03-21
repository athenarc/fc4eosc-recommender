import time
from typing import Dict, List, Optional

import pandas as pd
from darelabdb.recs_similarity_based.components.similarity.per_item_similarity_calculation import (
    calculate_similarities_of_embeddings,
    calculate_similarities_of_embeddings_batch,
    cosine_similarity_calculation_per_item,
)
from darelabdb.recs_similarity_based.components.similarity.SimilarityManagerABC import (
    SimilarityManager,
)
from darelabdb.utils_cache.CacheABC import Cache
from darelabdb.utils_schemas.item import item_id_type
from loguru import logger


class MetadataSimilarityManagerPerItem(SimilarityManager):
    """
    The MetadataSimilarityManagerPerItem class is responsible for the creation and caching of the items' metadata
    similarity. For each item the similarity manager will store the pairwise similarities with a given subset of the
    corpus items.
    """

    cache_key = "metadata_similarities"

    def __init__(self, cache_manager: Cache, recommender_id: str = None) -> None:
        """
        Args:
            cache_manager (Cache): The cache model in which the similarities will be stored.
            recommender_id (str): The id of the recommender that will be used to create the cache key.
        """
        if recommender_id is not None:
            self.cache_key = f"{self.cache_key}_{recommender_id}"
        self.cache_manager = cache_manager

    def is_initialised(self) -> bool:
        pass

    def initialise(
        self,
        embeddings: pd.DataFrame = None,
        similarities_cache: Dict[str, float] = None,
    ) -> None:
        """
        Checks if the item similarities already exists.
        If not it creates the similarities between the first item and the rest of the given embeddings.

        Args:
            embeddings (List[List[float]]): A dataframe with the ids and the embeddings of items.
            similarities_cache (Dict[<item_id1>:<item_id2>, similarity]): A dictionary with precalculated
                pairwise similarities.
        """
        # TODO check if the similarities of the item are initialized
        self.update(embeddings, similarities_cache)

    def update(
        self, embeddings: pd.DataFrame, similarities_cache: Dict[str, float] = None
    ) -> None:
        """
        Creates and stores the pairwise metadata similarity of the first item embedding with the rest of the
        given embeddings.

        Args:
            embeddings (DataFrame): A dataframe with the ids and the embeddings of items.
            similarities_cache (Dict[<item_id1>:<item_id2>, similarity]): A dictionary with precalculated
                pairwise similarities.
        """
        if embeddings is None:
            return None

        item_id = embeddings.index[0]
        similarities = calculate_similarities_of_embeddings(
            embeddings,
            cosine_similarity_calculation_per_item,
            similarities_cache,
        )

        # Store similarities
        self.cache_manager.set_json(
            self.cache_key,
            str(item_id),
            similarities,
        )

    def initialise_batch(
        self, embeddings_list: Optional[List[pd.DataFrame]] = None, proc_numb: int = 4
    ) -> None:
        """
        Checks if the text similarities already exist.
        If not it creates and stores the similarities between given items using multiprocessing (Recommended if available processes > 2).

        Args:
            embeddings_list (DataFrame): A dataframe with the ids and the embeddings of items.
            proc_numb (int): Number of processes used in the calculations
        """
        # TODO check if the similarities of the item are initialized
        self.update_batch(embeddings_list, proc_numb)

    def update_batch(
        self, embeddings_list: List[pd.DataFrame], proc_numb: int = 4
    ) -> None:
        """
        Takes as input all the pairwise calculations that will be calculated in batches. However, due to the
        multiprocessing similarities caching is not allowed. (Recommended if available processes > 2)

        Args:
            embeddings_list (List[DataFrame]): A list of dataframes with the ids and the embeddings of items.
            proc_numb (int): Number of processes used in the calculations
        """
        similarities = calculate_similarities_of_embeddings_batch(
            embeddings_list, cosine_similarity_calculation_per_item, proc_numb
        )

        start = time.time()
        for item_id, similarity in similarities:
            self.cache_manager.set_json(
                self.cache_key,
                str(item_id),
                similarity,
            )
        logger.info(f">>> Similarity storing took {time.time() - start} seconds")

    def get_similarities(self, items_ids: List[item_id_type]) -> pd.DataFrame:
        """
        Returns (pd.DataFrame): The similarities of an item with the approximate most similar items in the corpus of
        items.

        For example if items_ids = [1] and the ids of the similar items in the corpus are [3, 4, 5] the returned
        dataframe would look like
                      3     4    5
                1   0.2 | 0.4 | 0.8

        """

        if len(items_ids) > 1:
            raise ValueError(
                "Similarity managers per item do not support multiple item ids in get_similarities method!"
            )

        item_id = items_ids[0]

        similarities = self.cache_manager.get_json(self.cache_key, str(item_id))

        return pd.DataFrame(
            similarities,
            index=[item_id],
        )
