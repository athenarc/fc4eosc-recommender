from typing import List, Union

import numpy as np
from darelabdb.utils_schemas.item import Item
from loguru import logger
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


def tf_idf_vectorize(
    items: List[Item],
    item_vector_dimension: int = 100,
    l2_normalize: bool = False,
    max_df: Union[float, int] = 1.0,
    min_df: Union[float, int] = 1,
    max_features: int = None,
) -> (np.array, TfidfVectorizer, TruncatedSVD):
    """
    Vectorize the items' text attributes using the TF-IDF algorithm and apply PCA to reduce the dimensions.
    The vectorizer will take into account all the text attributes of the items.

    Args:
        items (List[Item]): A list of items that will be vectorized based on their text attributes
        item_vector_dimension (int): The final dimension of the vector representing each item.
        l2_normalize (bool): If L2 normalization will be applied (useful for cosine similarity)
        max_df (float | int): The maximum document frequency allowed for a word to be included in the vocabulary.
            If float (0,1) it's the maximum percentage of documents that a word appears. If int it's the maximum number
            of documents that the word appears.
        min_df (float | int): The minimum document frequency allowed for a word to be included in the vocabulary.
            If float (0,1) it's the minimum percentage of documents that a word appears. If int it's the minimum number
            of documents that the word appears.
        max_features (int): The total size of the vocabulary for tf-idf

    Returns:
        np.array: The vectorized items
        TfidfVectorizer: The vectorizer used
        TruncatedSVD: The PCA used
    """
    # Get the concatenated text attributes of the items
    items_text = [" ".join(item.text_attributes.values()) for item in items]

    # Count vectorized on all items
    vectorizer = TfidfVectorizer(
        max_features=max_features, max_df=max_df, min_df=min_df, dtype=np.float32
    )
    items_vectors = vectorizer.fit_transform(items_text)

    # PCA on the count vectorized items
    if item_vector_dimension > min(items_vectors.shape[0], items_vectors.shape[1]):
        item_vector_dimension = min(items_vectors.shape[0], items_vectors.shape[1])
        logger.warning(
            f"The given item_vector_dimension is invalid! The "
            f"value {item_vector_dimension} will be used instead."
        )

    svd = TruncatedSVD(n_components=item_vector_dimension)
    items_vectors = svd.fit_transform(items_vectors)

    if l2_normalize:
        items_vectors = normalize(items_vectors, norm="l2")

    return items_vectors, vectorizer, svd
