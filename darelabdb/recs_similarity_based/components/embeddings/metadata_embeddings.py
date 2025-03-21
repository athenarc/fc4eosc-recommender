from typing import List, Optional

import numpy as np
import pandas as pd
from darelabdb.utils_cache.CacheABC import Cache
from darelabdb.utils_schemas.item import (
    Item,
    complete_item_based_on_schema,
    get_metadata_values_of_attribute,
    get_superset_schema_of_items,
)
from loguru import logger
from sklearn.preprocessing import MultiLabelBinarizer


class MetadataEmbeddingsManager:
    """
    The TextEmbeddingManager class is responsible for the creation and caching of metadata embeddings.
    """

    cache_key = "metadata_embeddings"

    def __init__(self, cache_manager: Cache, recommender_id: str = None) -> None:
        """
        Args:
            cache_manager (Cache): The cache model in which the embeddings will be stored.
            recommender_id (str): The id of the recommender that will be used to create the cache key.
        """
        self.cache_manager = cache_manager
        if recommender_id is not None:
            self.cache_key = f"{self.cache_key}_{recommender_id}"

        self.items_schema = None

    def is_initialised(self) -> bool:
        """
        Checks if the metadata embeddings already exist.
        Returns:
            True if the embeddings exist, False otherwise.
        """
        return self.cache_manager.exists_df(self.cache_key)

    def initialise(self, items: Optional[List[Item]] = None) -> None:
        """
        Checks if the metadata embeddings already exist.
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
        Creates and stores the embeddings for each of the given items.

        Args:
            items (List[Item]): A list of items from which the embeddings will be created.
        """

        logger.info("Creating the metadata embeddings...")

        # Get the items schema
        self.items_schema = get_superset_schema_of_items(items)

        # Transform items into complete items (all the metadata values filled)
        complete_items = list(
            map(
                lambda item: complete_item_based_on_schema(item, self.items_schema),
                items,
            )
        )

        # Get the metadata attributes values of each item
        data = {
            item.item_id: {attr: val for attr, val in item.metadata_attributes.items()}
            for item in complete_items
        }
        items_metadata = pd.DataFrame.from_records(
            data=list(data.values()), index=data.keys()
        )

        # Get all the metadata attributes
        metadata_attributes = self.items_schema["metadata_attributes"]

        # Create the binarizers
        binarizers = {}
        partial_embeddings = []
        # For each metadata attribute (i.e. "category")
        for attribute in metadata_attributes:
            # Get the set of values of an attribute
            attribute_values = get_metadata_values_of_attribute(items, attribute)
            # Initialize binarizers for the attribute
            binarizers[attribute] = MultiLabelBinarizer(classes=list(attribute_values))
            # Transform item's metadata attribute to one-hot encoding
            partial_embeddings.append(
                binarizers[attribute].fit_transform(items_metadata[attribute])
            )

        # Store binarizers
        self.cache_manager.set_df(
            "metadata_binarizers",
            pd.DataFrame(data=list(binarizers.values()), index=list(binarizers.keys())),
        )

        # Concatenate encodings of all attributes
        embeddings = pd.DataFrame(
            data=np.concatenate(tuple(partial_embeddings), axis=1),
            index=items_metadata.index,
        )

        # Store embeddings
        self.cache_manager.set_df(self.cache_key, embeddings)

    def get_embeddings(self) -> pd.DataFrame:
        """
        Returns (DataFrame): A dataframe with the stored embeddings.
        """
        return self.cache_manager.get_df(self.cache_key)

    def delete_embeddings(self):
        """Deletes the metadata embeddings from the cache."""
        self.cache_manager.delete_on_prefix(prefix=self.cache_key)
