import multiprocessing
from functools import partial
from typing import List, Optional

import numpy as np
import pandas as pd
from darelabdb.recs_similarity_based.components.similarity.sdr_similarity import (
    calculate_sdr_similarities,
)
from darelabdb.recs_similarity_based.components.similarity.SimilarityManagerABC import (
    SimilarityManager,
)
from darelabdb.utils_cache.CacheABC import Cache
from darelabdb.utils_schemas.item import item_id_type
from loguru import logger
from tqdm import tqdm


class TextSimilarityManagerPerCorpus(SimilarityManager):
    """
    The TextSimilarityManagerPerCorpus class is responsible for the creation and caching of the items' text similarity.
    For each item the similarity manager will store the pairwise similarities with all the corpus items.
    """

    cache_key = "text_similarities"
    indexes_cache_key = "text_similarities_indexes"
    exist_cache_key = "text_similarities_exists"

    def __init__(
        self,
        cache_manager: Cache,
        recommender_id: str = None,
        proc_numb: int = 1,
        chunk_size: int = 20,
    ) -> None:
        """
        Args:
            cache_manager (Cache): The cache model in which the embeddings will be stored.
            recommender_id (str): The id of the recommender that will be used to create the cache key.
            proc_numb (int): The number of processes to use for the calculation of the similarities.
            chunk_size (int): The number of items to be processed in each process. Note that this number should
                be lower than number of items / proc_numb to utilize all the processes.
        """
        if recommender_id is not None:
            self.cache_key = f"{self.cache_key}_{recommender_id}"
            self.indexes_cache_key = f"{self.indexes_cache_key}_{recommender_id}"
            self.exist_cache_key = f"{self.exist_cache_key}_{recommender_id}"

        self.cache_manager = cache_manager
        self.proc_numb = proc_numb
        self.chunk_size = chunk_size

    def is_initialised(self) -> bool:
        """
        Checks if the text similarities already exist.
        Returns:
            True if the embeddings exist, False otherwise.
        """
        return (
            self.cache_manager.exists(self.exist_cache_key)
            and self.cache_manager.get(self.exist_cache_key) == 1
        )

    def initialise(self, embeddings: Optional[pd.DataFrame] = None) -> None:
        """
        Checks if the text similarities already exist.
        If not it creates and stores the similarities between given items.

        Args:
            embeddings (DataFrame): A dataframe with the ids and the embeddings of items.
        """
        if not self.is_initialised() and embeddings is not None:
            self.update(embeddings)
        elif not self.is_initialised() and embeddings is None:
            logger.error(f"{self.cache_key} do not exist in cache, cannot initialize.")
            raise KeyError(
                f"{self.cache_key} do not exist. Possible solution: Run the `update` method "
                "of the recommender providing the list of your items."
            )
        else:
            logger.info(f"Using the {self.cache_key} in cache.")

    def _pairwise_similarities_calculation(
        self, embeddings: pd.DataFrame
    ) -> pd.DataFrame:
        # We need the row number to calculate the upper triangular similarities only
        embeddings["row_index"] = np.arange(len(embeddings))
        chunk_embeddings_calculation = partial(
            calculate_chunk_embeddings, embeddings=embeddings
        )
        chunks = np.array_split(embeddings, max(len(embeddings) // self.chunk_size, 1))

        with multiprocessing.Pool(processes=self.proc_numb) as pool:
            similarities = tqdm(
                pool.imap(chunk_embeddings_calculation, chunks),
                desc="Pairwise Similarities",
                total=len(chunks),
            )
            # similarities = pool.map(chunk_embeddings_calculation, chunks)
            similarities = pd.concat(list(similarities)).filter(["similarities"])

        similarities_arr = np.array(similarities["similarities"].tolist())
        similarities_arr = np.triu(similarities_arr, k=1) + similarities_arr.T
        np.fill_diagonal(similarities_arr, 1)

        similarities["similarities"] = similarities_arr.tolist()

        return similarities

    def update(self, embeddings: pd.DataFrame) -> None:
        """
        Creates and stores the pairwise text similarity for the given embeddings.
        Args:
            embeddings (DataFrame): A dataframe with the ids and the embeddings of items.
        """

        logger.info(f"Creating the {self.cache_key}...")
        similarities = self._pairwise_similarities_calculation(embeddings)

        # Bring the similarities in a format that can be stored in the cache
        similarities = [
            (
                self.cache_key,
                str(item_index),
                np.array(row["similarities"]),
            )
            for item_index, row in similarities.iterrows()
        ]

        # Store similarities
        self.cache_manager.set_json(
            key=self.indexes_cache_key, index="", data=list(embeddings.index)
        )
        self.cache_manager.set_vectors(similarities)

        self.cache_manager.set(self.exist_cache_key, 1)

    # TODO unify with MetadataSimilarityManagerPerCorpus get_similarities method
    def get_similarities(self, items_ids: List[item_id_type]) -> pd.DataFrame:
        """
        Returns (pd.DataFrame): The similarities of an item with the corpus of items.

        For example if items_ids = [1, 2] and the ids of the items in the corpus are [1, 2, 3, 4, 5] the returned
        dataframe would look like
                     1     2     3     4    5
                1  0.5 | 0.3 | 0.2 | 0.4 | 0.8
                2  0.2 | 0.6 | 0.1 | 0.7 | 0.3

        """
        indexes = self.cache_manager.get_json(key=self.indexes_cache_key, index="")

        # Get the similarities for all items in items_ids
        vectors = self.cache_manager.get_vectors(
            self.cache_key, [str(item_id) for item_id in items_ids]
        )

        similarities = pd.DataFrame(
            data=np.array(vectors), index=items_ids, columns=indexes
        )

        return similarities


def calculate_chunk_embeddings(
    chunk: pd.DataFrame, embeddings: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculates the similarities of a subset of embeddings (chunk) with the given embeddings.
    Args:
        chunk (pd.DataFrame): A dataframe with the ids and the embeddings of items.
        embeddings (pd.DataFrame): A dataframe with the ids and the embeddings of items.

    """
    chunk["similarities"] = chunk.apply(
        lambda row: calculate_sdr_similarities(
            row["sentence_embeddings"], embeddings, row_index=row["row_index"]
        ),
        axis=1,
    )

    return chunk
