from typing import List, Tuple

import numpy as np
import pandas as pd
from darelabdb.recs_similarity_based.components.similarity.SimilarityManagerABC import (
    SimilarityManager,
)
from loguru import logger


# TODO different similar item per Similarity manager -> add similarity = 0 for non-calculated similarities?
# TODO same for history
# TODO we cannot return np.array in get_similarities. Indexes are necessary!


def calculate_similarities(
    similarity_manager: SimilarityManager,
    viewed_item_id,
    item_history,
    item_history_weight,
) -> np.array:
    similarities = similarity_manager.get_similarities([viewed_item_id] + item_history)
    w_avg_similarities = (
        similarities.iloc[0] * (1 - item_history_weight)
        + np.array(similarities.iloc[1:]).sum(axis=0) * item_history_weight
    )

    return w_avg_similarities


def get_similar_items(
    viewed_item_id,
    item_history,
    item_history_weight: float,
    similarity_managers_with_weights: List[Tuple[SimilarityManager, float]],
) -> pd.Series:
    check_given_weights([weight for _, weight in similarity_managers_with_weights])

    weighted_avg_similarities = [
        calculate_similarities(
            similarity_manager, viewed_item_id, item_history, item_history_weight
        )
        * weight
        for similarity_manager, weight in similarity_managers_with_weights
    ]

    candidates = pd.Series(
        np.array(weighted_avg_similarities).sum(axis=0),
        index=weighted_avg_similarities[0].index,
        # index=similarity_managers_with_weights[0][0].get_indexes(),
    )

    return candidates.drop([viewed_item_id] + item_history, errors="ignore")


def check_given_weights(weights: List[float]):
    weight_sum = sum(weights)
    if weight_sum != 1:
        logger.warning(
            f"The weights of the similarity managers sum to {weight_sum} instead of 1."
        )
