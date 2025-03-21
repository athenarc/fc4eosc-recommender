from typing import Union

import numpy as np
from darelabdb.recs_similarity_based.components.clustering.vectorizer import (
    tf_idf_vectorize,
)
from darelabdb.utils_schemas.item import Item
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

# TODO default value for clusters = None -> find the best value based on corpus size
# TODO minimum number of items in a cluster


def kmeans_with_tf_idf_clustering(
    items: list[Item],
    item_vector_dimension: int = 100,
    clusters_num: int = 10,
    max_df: Union[float, int] = 1.0,
    min_df: Union[float, int] = 1,
    max_features: int = None,
) -> (list[list[Item]], TfidfVectorizer, TruncatedSVD, KMeans):
    """
    Divides the given items into clusters. Kmeans algorithm is used for the clustering. Each item is represented by a
    vector produced by the TF-IDF algorithm, after applying PCA to reduce its dimensions.

    Args:
        items (list[Item]): The list of items to cluster.
        item_vector_dimension (int): The final dimension of the vector representing each item.
        clusters_num (int): The number of clusters that will be created.
        max_df (float | int): The maximum document frequency allowed for a word to be included in the vocabulary.
            If float (0,1) it's the maximum percentage of documents that a word appears. If int it's the maximum number
            of documents that the word appears.
        min_df (float | int): The minimum document frequency allowed for a word to be included in the vocabulary.
            If float (0,1) it's the minimum percentage of documents that a word appears. If int it's the minimum number
            of documents that the word appears.
        max_features (int): The total size of the vocabulary for tf-idf

    Returns (list[list[item_id_type]], TfidfVectorizer, KMeans):
        A list with the items in each cluster.

    """
    items_vectors, vectorizer, svd = tf_idf_vectorize(
        items,
        item_vector_dimension,
        max_df=max_df,
        min_df=min_df,
        max_features=max_features,
    )

    if clusters_num > items_vectors.shape[0]:
        clusters_num = max(2, int(items_vectors.shape[0] / 4))
        logger.warning(
            f"The given number of clusters is bigger than the number of items! The "
            f"value {clusters_num} will be used instead."
        )

    # Run k-means in the items' vectors
    kmeans = KMeans(n_clusters=clusters_num)
    items_clusters = kmeans.fit_predict(items_vectors)

    # Create a list with the item indexes of every cluster
    item_indexes_per_cluster = [
        np.where(items_clusters == value)[0].tolist()
        for value in np.unique(items_clusters)
    ]
    # Replace the indexes with the Item class of the items
    items_per_cluster = []
    for cluster_item_indexes in item_indexes_per_cluster:
        items_per_cluster.append(
            [items[item_index] for item_index in cluster_item_indexes]
        )

    return items_per_cluster, vectorizer, svd, kmeans
