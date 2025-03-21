from typing import Callable, List, Union

import pandas as pd


def filter_candidates(
    candidates: pd.Series, filtering_methods: Union[Callable, List[Callable]]
) -> pd.Series:
    """
    Filters the candidates based on the given filtering methods.
    Args:
        candidates: A pandas Series of the candidate recommendations (ids as index, scores as values)
        filtering_methods: A list of filtering methods that will be applied to each candidate. Should take as input
            the id of the item and return True if the item should be kept, False otherwise.

    Returns:
        The same pandas Series with the filtered candidates.
    """
    if isinstance(filtering_methods, Callable):
        filtering_methods = [filtering_methods]

    remaining_candidates = candidates
    for filtering_method in filtering_methods:
        remaining_candidates = remaining_candidates[
            remaining_candidates.index.map(filtering_method)
        ]

    return remaining_candidates
