from typing import List, Optional

import pandas as pd
from darelabdb.nlp_embeddings.embedding_methods.TextEmbeddingMethodABC import (
    TextEmbeddingMethod,
)
from darelabdb.recs_similarity_based.components.embeddings.sentence_filtering.SentenceFilteringABC import (
    SentenceFiltering,
)
from darelabdb.recs_similarity_based.components.text_processing.TextProcessor import (
    TextProcessor,
    text_preprocessing,
)
from darelabdb.utils_cache.CacheABC import Cache
from darelabdb.utils_schemas.item import Item
from loguru import logger
from tqdm import tqdm


class TextEmbeddingsManager:
    """
    The TextEmbeddingManager class is responsible for the creation and caching of text embeddings.
    """

    cache_key = "text_embeddings"

    def __init__(
        self,
        cache_manager: Cache,
        text_embedding_method: TextEmbeddingMethod,
        sentence_filtering_method: Optional[SentenceFiltering] = None,
        recommender_id: Optional[str] = None,
    ) -> None:
        """
        Args:
            cache_manager (Cache): The cache model in which the embeddings will be stored.
            text_embedding_method (TextEmbeddingMethod): The class responsible for creating the embedding of a
                                                            string.
            sentence_filtering_method: Method that will be used for filtering out non-informative sentences from the
                text attributes of the items
            recommender_id (str): The id of the recommender that will be used to create the cache key.
        """
        self.cache_manager = cache_manager
        if recommender_id is not None:
            self.cache_key = f"{self.cache_key}_{recommender_id}"

        self.text_embedding_method = text_embedding_method
        self.sentence_filtering_method = sentence_filtering_method
        self.text_processor = TextProcessor()

    def is_initialised(self) -> bool:
        """
        Checks if the text embeddings already exist.
        Returns:
            True if the embeddings exist, False otherwise.
        """
        return self.cache_manager.exists_df(self.cache_key)

    def initialise(self, items: Optional[List[Item]] = None) -> None:
        """
        Checks if the text embeddings already exist.
        If not it creates and stores the embeddings for each of the given items.

        Args:
            items (List[Item]): A list of items from which the embeddings will be created. If none it means that the
                                embeddings already exist in cache.
        """
        if not self.is_initialised() and items is not None:
            self.update(items)
        elif not self.is_initialised() and items is None:
            logger.error(f"{self.cache_key} do not exist in cache, cannot initialize.")
            raise KeyError(
                f"{self.cache_key} do not exist. Possible solution: Run the `update` method "
                "of the recommender and provide the list of your items."
            )
        else:
            logger.info(f"Using the {self.cache_key} in cache.")

    def update(self, items: List[Item]) -> None:
        """
        Updates the embeddings for each of the given items even if they exist in cache.
        Args:
            items:  A list of items from which the embeddings will be created.
        """
        logger.info(f"Creating the {self.cache_key}...")

        # Get the text attributes values of each item
        items_text = pd.DataFrame.from_records(
            [
                {
                    "id": item.item_id,
                    "sentences": text_preprocessing(
                        item.text_attributes,
                        self.text_processor,
                        self.sentence_filtering_method,
                    ),
                }
                for item in tqdm(
                    items, desc="Preprocessing text attributes", mininterval=180
                )
            ]
        )

        # Generate the embeddings of the sentences
        items_text_with_embeddings = self.text_embedding_method.get_items_embedding(
            items_text
        )

        # Create a dataframe with the embeddings of the items and the item ids as index
        embeddings = items_text_with_embeddings.filter(["sentence_embeddings", "id"])
        embeddings.set_index("id", inplace=True)

        # Store embeddings
        self.cache_manager.set_df(key=self.cache_key, data=embeddings)

    def get_embeddings(self) -> pd.DataFrame:
        """
        Returns (DataFrame): A dataframe with the stored embeddings.
        """
        return self.cache_manager.get_df(self.cache_key)

    def delete_embeddings(self):
        """Deletes the text embeddings from the cache."""
        self.cache_manager.delete_on_prefix(prefix=self.cache_key)
