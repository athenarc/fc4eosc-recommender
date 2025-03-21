from typing import Any, List, Union

import faiss
import numpy as np
from darelabdb.recs_similarity_based.components.clustering.vectorizer import (
    tf_idf_vectorize,
)
from darelabdb.utils_schemas.item import Item, item_id_type


class NearestNeighbor:
    """Class responsible for finding the nearest neighbors of an item based on its vector representation.
    The vector representation is produced by the TF-IDF algorithm and the similarity is calculated using the cosine.
    """

    def __init__(self):
        self.index = None
        self.items_vectors = None
        self.id_to_index_mapping = None
        self.index_to_id_mapping = None

    def initialize(
        self,
        items: list[Item],
        item_vector_dimension: int = 100,
        l2_normalize: bool = True,
        max_df: Union[float, int] = 1.0,
        min_df: Union[float, int] = 1,
        max_features: int = None,
    ) -> None:
        """
        Initializes the nearest neighbor structure with the given items.
        Args:
            items (list[Item]): The items to be used for the initialization.
            item_vector_dimension: The dimension of the vector representing the items. Ideally a multiple of 4
                that faiss is optimized for.
            l2_normalize (bool): If L2 normalization will be applied (useful for cosine similarity)
            max_df (float | int): The maximum document frequency allowed for a word to be included in the vocabulary.
                If float (0,1) it's the maximum percentage of documents that a word appears. If int it's the maximum number
                of documents that the word appears.
            min_df (float | int): The minimum document frequency allowed for a word to be included in the vocabulary.
                If float (0,1) it's the minimum percentage of documents that a word appears. If int it's the minimum number
                of documents that the word appears.
            max_features (int): The total size of the vocabulary for tf-idf
        """
        self.items_vectors, _, _ = tf_idf_vectorize(
            items, item_vector_dimension, l2_normalize, max_df, min_df, max_features
        )
        self.id_to_index_mapping = {item.item_id: ind for ind, item in enumerate(items)}
        self.index_to_id_mapping = {ind: item.item_id for ind, item in enumerate(items)}

        self.index = faiss.IndexFlatIP(self.items_vectors.shape[1])
        self.index.add(self.items_vectors)

    def search(self, item_id: item_id_type, k: int = 5) -> List[item_id_type]:
        """
        Finds the k nearest neighbors of the given item.
        Args:
            item_id (item_id_type): The item id for which the nearest neighbors will be found.
            k (int): The number of nearest neighbors to be found.

        Returns:
            List[item_id_type]: The ids of the k nearest neighbors.
        """
        try:
            item_vector = self.items_vectors[self.id_to_index_mapping[item_id]]
        except KeyError:
            raise KeyError(f"The item with id {item_id} was not found in the index.")

        distances, results = self.index.search(np.array([item_vector]), k + 1)

        ret_ids = [self.index_to_id_mapping[ind] for ind in results[0] if ind != -1]

        if item_id not in ret_ids:
            ret_ids = ret_ids[:-1]
        else:
            ret_ids.remove(item_id)

        return ret_ids


if __name__ == "__main__":
    items = []

    for i in range(10):
        items.append(
            Item(
                item_id=f"id_{i}",
                text_attributes={"title": f"title {i}", "abstract": f"abstract {i}"},
            )
        )

    nn = NearestNeighbor()
    nn.initialize(items)

    nn.search(items[0].item_id, 5)
