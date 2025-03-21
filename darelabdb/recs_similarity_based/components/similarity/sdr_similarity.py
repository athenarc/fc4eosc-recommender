import multiprocessing
from itertools import repeat
from typing import List

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def calculate_sdr_similarity(
    item_embeddings_a: np.array, item_embeddings_b: np.array
) -> float:
    """
    Returns the similarity between two lists of embeddings.
    Args:
        item_embeddings_a (np.array[float]): The list of embeddings for an item.
        item_embeddings_b (np.array[float]): The list of embeddings for an item.

    Returns (float): The text similarity between the given embeddings.

    """
    pairwise_similarities = cosine_similarity(item_embeddings_a, item_embeddings_b)
    return np.average(np.max(pairwise_similarities, axis=1))


def calculate_sdr_similarities(
    item_embedding: np.array,
    items_embeddings: pd.DataFrame,
    row_index: int = -1,
) -> List[float]:
    """
    Calculates the similarity between a given item embedding and a corpus of embeddings.
    Args:
        item_embedding (np.array[float]): The text embedding of an item.
        items_embeddings (DataFrame): The text embeddings for a corpus of items.
        row_index (int): The row index of the item embedding (not the id). If -1 is given,
            then we calculate the similarities for all the items.

    Returns (List[float]): A list of size <items_number> with the pairwise embeddings similarities.
    """
    similarities = [0.0] * (
        row_index + 1
    )  # Used in case we want to calculate the upper triangular
    remaining_embeddings = items_embeddings.iloc[row_index + 1 :]

    for _, row in remaining_embeddings.iterrows():
        similarities.append(
            calculate_sdr_similarity(item_embedding, row["sentence_embeddings"])
        )

    return similarities
