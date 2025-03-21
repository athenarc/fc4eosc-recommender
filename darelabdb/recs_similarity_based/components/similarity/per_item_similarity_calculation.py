import multiprocessing
import os
import pickle
import tempfile
import time
from itertools import chain, islice, repeat
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from darelabdb.recs_similarity_based.components.similarity.sdr_similarity import (
    calculate_sdr_similarities,
)
from darelabdb.utils_schemas.item import item_id_type
from loguru import logger
from sklearn.metrics.pairwise import cosine_similarity


def cosine_similarity_calculation_per_item(embeddings: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the cosine similarities between the first item and the rest of the items in the embeddings.
    """
    similarities = cosine_similarity(
        [embeddings.to_numpy()[0]], embeddings.to_numpy()[1:]
    )[0]

    return pd.DataFrame(
        similarities, columns=["similarities"], index=embeddings.index[1:]
    )


def sdr_similarity_calculation_per_item(embeddings: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the pairwise similarities between the first item and the rest of the items in the embeddings.
    """
    similarities = calculate_sdr_similarities(
        np.array(embeddings.iloc[0]["sentence_embeddings"]),
        embeddings.iloc[1:],
    )

    similarities = pd.DataFrame(
        {"similarities": similarities}, index=embeddings.index[1:]
    )

    return similarities


def calculate_similarities_of_embeddings(
    embeddings: pd.DataFrame,
    similarity_method: Callable[[pd.DataFrame, int], pd.DataFrame],
    similarities_cache: Dict[str, float] = None,
) -> Dict[item_id_type, float]:
    """
    Calculate the similarities of the first item with the rest of the items in the embeddings.
    The similarities are calculated using the similarity_method.

    Args:
        embeddings (pd.DataFrame): The DataFrame containing the embeddings of the items.
            Its structure depends on the similarity_method.
        similarity_method (Callable): A methods that takes as input the embeddings and returns a DataFrame
            with the similarities.
        similarities_cache (Dict): A dictionary containing the similarities that have already been calculated.

    Returns:
        (Dict): A dictionary containing the similarities of the first item with the rest of the items in the embeddings.
    """
    item_id = embeddings.index[0]

    if similarities_cache is None:
        # The similarities cache will be updated but ignored and not returned
        similarities_cache = {}

    # Find calculated similarities and remove them from cache
    precalculated_similarities = {}
    for neigh_item_id in list(embeddings.index[1:]):
        if f"{neigh_item_id}:{item_id}" in similarities_cache:
            precalculated_similarities[neigh_item_id] = similarities_cache[
                f"{neigh_item_id}:{item_id}"
            ]
            del similarities_cache[f"{neigh_item_id}:{item_id}"]

    if len(precalculated_similarities) < embeddings.shape[0] - 1:
        # Remove item embeddings with calculated similarities
        embeddings = embeddings[
            ~embeddings.index.isin(list(precalculated_similarities.keys()))
        ]

        # Calculate the non calculated similarities
        item_similarities = (
            similarity_method(embeddings) if not embeddings.empty else pd.DataFrame()
        )
    else:
        item_similarities = pd.DataFrame({"similarities": []})

    # Append the precalculated similarities
    if len(precalculated_similarities) > 0:
        item_similarities = pd.concat(
            [
                item_similarities,
                pd.DataFrame(
                    list(precalculated_similarities.values()),
                    index=list(precalculated_similarities.keys()),
                    columns=["similarities"],
                ),
            ]
        )

    # Update the similarities cache
    similarities_cache.update(
        {
            f"{item_id}:{index}": row["similarities"]
            for index, row in item_similarities.iterrows()
        }
    )

    return item_similarities.to_dict(orient="dict")["similarities"]


def calculate_similarities_of_embeddings_batch(
    embeddings_list: List[pd.DataFrame], similarity_method: Callable, proc_numb: int = 4
) -> Optional[List[Tuple[item_id_type, Dict[item_id_type, float]]]]:
    """
    Calculate the similarities of the first item with the rest of the items in the embeddings in batches.
    The similarities are calculated using the similarity_method.

    Args:
        embeddings_list (List[pd.DataFrame]): A list of DataFrames containing the embeddings of the items.
            The structure of the DataFrames depends on the similarity_method.
        similarity_method (Callable): A methods that takes as input the embeddings and returns a DataFrame
        proc_numb (int): The number of processes used in the calculations.

    Returns:
        List[Dict]: A list of dictionaries containing the similarities of the first item with the rest of the
            items in the embeddings.
    """
    if len(embeddings_list) == 0:
        return None

    chunk_size = (
        (len(embeddings_list) // proc_numb) + 1
        if len(embeddings_list) > proc_numb
        else len(embeddings_list)
    )

    temp_dir = tempfile.TemporaryDirectory(dir="./")
    ret_paths = create_and_store_chunks(
        embeddings_list, chunk_size, dir_path=temp_dir.name
    )

    embeddings_ids = [emb.index[0] for emb in embeddings_list]

    del embeddings_list

    logger.info(
        f">>> Starting multiprocess similarities calculation "
        f"with {multiprocessing.get_start_method()} strategy..."
    )

    start = time.time()
    with multiprocessing.Pool(processes=proc_numb) as pool:
        similarities = pool.starmap(
            similarity_calculation_chunked,
            zip(
                ret_paths,
                repeat(similarity_method),
            ),
        )
    logger.info(
        f">>> Multiprocess similarities calculation took {time.time() - start} seconds"
    )

    temp_dir.cleanup()

    return zip(embeddings_ids, chain.from_iterable(similarities))


def similarity_calculation_chunked(
    embeddings_chunk_path: str,
    similarity_method: Callable[[pd.DataFrame, int], pd.DataFrame],
) -> List[Dict[item_id_type, float]]:
    """
    Helper methods that executes the similarity method over a chunk of embeddings.
    Args:
        embeddings_chunk_path: The path of the pickle chunk of embeddings to calculate similarities
        similarity_method: The methods used for calculating the similarity (cosine_similarity_calculation_per_item,
            sdr_similarity_calculation_per_item)

    Returns:
        A list of dictionaries containing the similarities of given items with the neighbor items
    """
    pid = os.getpid()
    logger.info(f">>> Starting process with pid {pid}")
    with open(embeddings_chunk_path, "rb") as f:
        embeddings_chunk = pickle.load(f)

    ret_similarities = []
    embeddings_len = len(embeddings_chunk)

    for ind, embeddings in enumerate(embeddings_chunk):
        if ind % 100 == 0:
            logger.info(
                f">>> PID {pid} - Similarities calculated {ind}/{embeddings_len}"
            )
        ret_similarities.append(
            calculate_similarities_of_embeddings(embeddings, similarity_method)
        )

    return ret_similarities


def create_and_store_chunks(iterable: Iterable, size: int, dir_path: str) -> List[str]:
    """
    Splits the input iterable into chunks of size. No padding is applied.
    Then stores them under the specified directory as pickle files.
    Args:
        iterable (Iterable): The iterable to split
        size (int): The size of each chunk
        dir_path (str): The directory that the pickle chunks will be stored
    """
    start = time.time()
    dir_path = dir_path[:-1] if dir_path[-1] == "/" else dir_path

    iterable = iter(iterable)
    chunks = list(iter(lambda: tuple(islice(iterable, size)), ()))

    ret_paths = []
    for ind, chunk in enumerate(chunks):
        with open(f"{dir_path}/chunk_{ind}.p", "wb") as f:
            pickle.dump(chunk, f)
        ret_paths.append(f"{dir_path}/chunk_{ind}.p")

    logger.info(f">>> Chunk creation took: {time.time() - start} seconds")
    return ret_paths
