import time
from typing import Callable, Dict, List, Optional

from darelabdb.nlp_embeddings.embedding_methods.SBERTEmbedding import SBERTEmbedding
from darelabdb.nlp_embeddings.embedding_methods.TextEmbeddingMethodABC import (
    TextEmbeddingMethod,
)
from darelabdb.recs_similarity_based.components.clustering.nearest_neighbor import (
    NearestNeighbor,
)
from darelabdb.recs_similarity_based.components.embeddings.metadata_embeddings import (
    MetadataEmbeddingsManager,
)
from darelabdb.recs_similarity_based.components.embeddings.sentence_filtering.SentenceFilteringABC import (
    SentenceFiltering,
)
from darelabdb.recs_similarity_based.components.embeddings.text_embeddings import (
    TextEmbeddingsManager,
)
from darelabdb.recs_similarity_based.components.logging.LoggerABC import Logger
from darelabdb.recs_similarity_based.components.similarity import similarity_aggregation
from darelabdb.recs_similarity_based.components.similarity.metadata_similarity_manager.metadata_similarity_manager_per_item import (
    MetadataSimilarityManagerPerItem,
)
from darelabdb.recs_similarity_based.components.similarity.text_similarity_manager.text_similarity_manager_per_item import (
    TextSimilarityManagerPerItem,
)
from darelabdb.recs_similarity_based.recommenders.filtering import filter_candidates
from darelabdb.utils_cache.CacheABC import Cache
from darelabdb.utils_cache.InMemory import InMemoryCache
from darelabdb.utils_cache.Mongo import MongoCache
from darelabdb.utils_cache.Postgres import PostgresCache
from darelabdb.utils_schemas.item import Item
from darelabdb.utils_schemas.item_recommendation import ItemRecommendation
from darelabdb.utils_schemas.user_state import UserState
from loguru import logger
from tqdm import tqdm


# TODO add NearestNeighbor item_vector_dimension as a parameter to recommender args?
class ApproximateSimilarityItemRecommender:
    def __init__(
        self,
        recommender_id: str = None,
        embeddings_cache_manager: Optional[Cache] = None,
        similarities_cache_manager: Optional[Cache | MongoCache | PostgresCache] = None,
        metadata_weight: Optional[float] = 0.25,
        item_history_weight: Optional[float] = 0.25,
        nearest_neighbors: Optional[int] = 60,
        tf_idf_vectorizer_settings: Dict = None,
        text_embedding_method: Optional[TextEmbeddingMethod] = SBERTEmbedding(),
        sentence_filtering_method: Optional[SentenceFiltering] = None,
        recommendations_filtering_methods: Optional[List[Callable]] = None,
        loggers: Optional[List[Logger]] = None,
        proc_numb: Optional[int] = 1,
        keep_embeddings: Optional[bool] = True,
        inference_only: bool = False,
    ):
        """
        The item-item recommender based on approximate similarity. Responsible for initialising the required managers
        (for the embeddings and the similarities of the items) and providing recommendations based on the user state.

        Args:
            recommender_id: An id to differentiate between other recommenders. Needs to be provided if persistence
                between runs is required.
            embeddings_cache_manager: The cache manager to use for storing the embeddings.
                If None, an in-memory cache manager will be used.
                Possible values: None, InMemoryCache(), RedisCache()
            similarities_cache_manager: The cache manager to use for storing the similarities.
                If None, an in-memory cache manager will be used. Can be the same as cache_manager_embeddings.
                Possible values: None, InMemoryCache(), RedisCache(), MongoCache(), PostgresCache()
            metadata_weight: The weight given to metadata vs. text attributes (note: text_weight = 1 - metadata_weight)
            item_history_weight: The weight given to the user history vs. the currently viewed item`
            nearest_neighbors: The number of nearest neighbors to consider when calculating the pairwise similarities
            tf_idf_vectorizer_settings: A dictionary holding the parameters for the tf_idf vectorizer used in nearest
                neighbors. Parameters: item_vector_dimension, l2_normalize, max_df, min_df, max_features
            text_embedding_method: Method that will embed the text attributes of the items.
            sentence_filtering_method: Method that will be used for filtering out non-informative sentences from the
                text attributes of the items
            recommendations_filtering_methods: A list of filtering methods that will be applied to each item id that is
                candidate for recommendations. Should take as input the id of the item and return True if the item
                should be kept, False otherwise.
            loggers: A list of loggers that will be used to log the recommendations created. Available: StdoutLogger,
                FileLogger, MongoLogger
            proc_numb: The number of processes to use for the calculation of the similarities.
            keep_embeddings: If True, the embeddings will be kept in the cache. If False, the embeddings will be
                deleted.
            inference_only: If True the model will only be used to generate recommendations, not initialise internal
                structures
        """
        if recommender_id is None:
            # If it is none add the memory address to make the id unique
            recommender_id = "item_recommender_" + str(id(self))
            logger.warning(
                f"No recommender id provided. Using {recommender_id} as id. Recommender id is required "
                f"if persistence between runs is needed."
            )

        if embeddings_cache_manager is None and not inference_only:
            logger.warning(
                "No embeddings cache manager provided. An in-memory cache manager will be used (no persistence)."
            )
            embeddings_cache_manager = InMemoryCache()

        if similarities_cache_manager is None:
            logger.warning(
                "No similarities cache manager provided. An in-memory cache manager will be used (no persistence)."
            )
            similarities_cache_manager = InMemoryCache()

        self.metadata_weight = metadata_weight
        self.item_history_weight = item_history_weight
        self.nearest_neighbors = nearest_neighbors
        self.tf_idf_vectorizer_settings = (
            tf_idf_vectorizer_settings if tf_idf_vectorizer_settings else {}
        )

        self.text_embeddings = (
            TextEmbeddingsManager(
                embeddings_cache_manager,
                text_embedding_method,
                sentence_filtering_method,
                recommender_id=recommender_id,
            )
            if not inference_only
            else None
        )

        self.metadata_embeddings = (
            MetadataEmbeddingsManager(
                embeddings_cache_manager, recommender_id=recommender_id
            )
            if not inference_only
            else None
        )
        self.keep_embeddings = keep_embeddings

        self.text_similarity = TextSimilarityManagerPerItem(
            similarities_cache_manager,
            recommender_id=recommender_id,
        )
        self.metadata_similarity = MetadataSimilarityManagerPerItem(
            similarities_cache_manager, recommender_id=recommender_id
        )
        self.proc_numb = proc_numb

        self.filtering_methods = recommendations_filtering_methods
        self.loggers = loggers

        self.nn = NearestNeighbor() if not inference_only else None

    def initialise(self, items: Optional[List[Item]] = None) -> None:
        # Initialize embeddings
        start = time.time()
        self.text_embeddings.initialise(items)
        logger.info(
            f">>> Text embeddings initialization took: {time.time() - start} seconds"
        )

        start = time.time()
        self.metadata_embeddings.initialise(items)
        logger.info(
            f">>> Metadata embeddings initialization took: {time.time() - start} seconds"
        )

        # Get embeddings
        text_embds = self.text_embeddings.get_embeddings()
        metadata_embds = self.metadata_embeddings.get_embeddings()

        start = time.time()
        self.nn.initialize(items)
        logger.info(
            f">>> Nearest neighbors initialization took: {time.time() - start} seconds"
        )

        # Initialize the caches with the already calculated similarities
        metadata_similarities_cache = {}
        text_similarities_cache = {}
        text_similarity_calculations = []
        metadata_similarity_calculations = []

        time_monitors = {
            "nn_search": 0,
            "metadata_similarity": 0,
            "locating_text_embeddings": 0,
        }
        start = time.time()
        for item in tqdm(
            items, desc="Approximate pairwise similarities:", mininterval=180
        ):
            # Get the approximate nearest neighbors of the current item
            start_internal = time.time()
            neighs = self.nn.search(item.item_id, k=self.nearest_neighbors)
            time_monitors["nn_search"] += time.time() - start_internal

            # Initialize the metadata similarities of the current item
            start_internal = time.time()
            if not self._is_multiprocess_similarity_calculation():
                # Initialize the text similarities of the current item
                self.metadata_similarity.initialise(
                    embeddings=metadata_embds.loc[[item.item_id] + neighs],
                    similarities_cache=metadata_similarities_cache,
                )
            else:
                # Prepare the similarity calculations to be executed in parallel
                metadata_similarity_calculations.append(
                    metadata_embds.loc[[item.item_id] + neighs]
                )
            time_monitors["metadata_similarity"] += time.time() - start_internal

            start_internal = time.time()
            if not self._is_multiprocess_similarity_calculation():
                # Initialize the text similarities of the current item
                self.text_similarity.initialise(
                    embeddings=text_embds.loc[[item.item_id] + neighs],
                    similarities_cache=text_similarities_cache,
                )
            else:
                # Prepare the similarity calculations to be executed in parallel
                text_similarity_calculations.append(
                    text_embds.loc[[item.item_id] + neighs]
                )
            time_monitors["locating_text_embeddings"] += time.time() - start_internal

        print("### Profiling Similarity Loop ###")
        print(f"> NN Search {time_monitors['nn_search']} seconds")
        print(f"> Metadata {time_monitors['metadata_similarity']} seconds")
        print(
            f"> Locating text embeddings {time_monitors['locating_text_embeddings']} seconds"
        )

        if self._is_multiprocess_similarity_calculation():
            logger.info("Calculating metadata similarities in parallel")
            self.metadata_similarity.initialise_batch(
                metadata_similarity_calculations, proc_numb=self.proc_numb
            )
            logger.info("Finished calculating metadata similarities in parallel")
        if self._is_multiprocess_similarity_calculation():
            logger.info("Calculating text similarities in parallel")
            self.text_similarity.initialise_batch(
                text_similarity_calculations, proc_numb=self.proc_numb
            )
            logger.info("Finished calculating text similarities in parallel")

        logger.info(f">>> Pairwise similarities took: {time.time() - start} seconds")

        if not self.keep_embeddings:
            self.text_embeddings.delete_embeddings()
            self.metadata_embeddings.delete_embeddings()

    def update(self, items: List[Item]):
        # NOTE: The ApproximateSimilarityItemRecommender cannot update -> changes in a set of items would result
        # in different approximate neighbors. All the similarities must be re-calculated.
        self.initialise(items)

    def add_item(self, item: Item) -> None:
        # Possibly will not be implemented
        pass

    def recommend(
        self, user_state: UserState, recs_num: int
    ) -> List[ItemRecommendation]:
        if len(user_state.item_history) > 0:
            logger.warning(
                "Item history is not supported by the ApproximateSimilarityItemRecommender."
            )
            user_state.item_history = []

        candidates = similarity_aggregation.get_similar_items(
            viewed_item_id=user_state.viewed_item_id,
            item_history=user_state.item_history,
            item_history_weight=self.item_history_weight,
            similarity_managers_with_weights=[
                (self.text_similarity, 1 - self.metadata_weight),
                (self.metadata_similarity, self.metadata_weight),
            ],
        )

        if self.filtering_methods is not None:
            # Filter out items that do not pass the filtering methods
            candidates = filter_candidates(candidates, self.filtering_methods)

        # Order item by similarity score
        candidates = candidates.sort_values(ascending=False)

        recommendations = [
            ItemRecommendation(item_id=item_id, score=similarity_score)
            for item_id, similarity_score in candidates[:recs_num].items()
        ]

        self._log(user_state=user_state, recommendations=recommendations)

        return recommendations

    def _log(self, user_state: UserState, recommendations: List[ItemRecommendation]):
        if self.loggers is not None:
            for log in self.loggers:
                log.log_item_recommendation(
                    user_state=user_state, recommendations=recommendations
                )

    def _is_multiprocess_similarity_calculation(self):
        return True if self.proc_numb > 2 else False


if __name__ == "__main__":
    similarities_cache_manager = PostgresCache(
        db_name="fc4eosc",
        specific_schema="recsys_schema",
    )

    gold_recommender = ApproximateSimilarityItemRecommender(
        recommender_id="faircore_similarity_based_rs",
        similarities_cache_manager=similarities_cache_manager,
        inference_only=True,
    )

    print(
        gold_recommender.recommend(
            user_state=UserState(
                viewed_item_id="doi_________::730603d4bd7157d673f75e0ffb9e39ed"
            ),
            recs_num=5,
        )
    )
