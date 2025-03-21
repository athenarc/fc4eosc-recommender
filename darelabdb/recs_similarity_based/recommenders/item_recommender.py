from typing import Callable, List, Optional

from darelabdb.nlp_embeddings.embedding_methods.SBERTEmbedding import SBERTEmbedding
from darelabdb.nlp_embeddings.embedding_methods.TextEmbeddingMethodABC import (
    TextEmbeddingMethod,
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
from darelabdb.recs_similarity_based.components.similarity.metadata_similarity_manager.metadata_similarity_manager_per_corpus import (
    MetadataSimilarityManagerPerCorpus,
)
from darelabdb.recs_similarity_based.components.similarity.text_similarity_manager.text_similarity_manager_per_corpus import (
    TextSimilarityManagerPerCorpus,
)
from darelabdb.recs_similarity_based.recommenders.filtering import filter_candidates
from darelabdb.utils_cache.CacheABC import Cache
from darelabdb.utils_cache.InMemory import InMemoryCache
from darelabdb.utils_schemas.item import Item
from darelabdb.utils_schemas.item_recommendation import ItemRecommendation
from darelabdb.utils_schemas.user_state import UserState
from loguru import logger


class ItemRecommender:
    def __init__(
        self,
        recommender_id: str = None,
        cache_manager: Optional[Cache] = None,
        metadata_weight: Optional[float] = 0.25,
        item_history_weight: Optional[float] = 0.25,
        text_embedding_method: Optional[TextEmbeddingMethod] = SBERTEmbedding(),
        sentence_filtering_method: Optional[SentenceFiltering] = None,
        recommendations_filtering_methods: Optional[List[Callable]] = None,
        loggers: Optional[List[Logger]] = None,
        proc_numb: Optional[int] = 1,
        keep_embeddings: Optional[bool] = True,
    ):
        """
        The item-item recommender based on similarity. Responsible for initialising the required managers
        (for the embeddings and the similarities of the items) and providing recommendations based on the user state.

        Args:
            recommender_id: An id to differentiate between other recommenders. Needs to be provided if persistence
                between runs is required.
            cache_manager: The cache manager to use. If None, an in-memory cache manager will be used.
                Possible values: None, InMemoryCache(), RedisCache()
            metadata_weight: The weight given to metadata vs. text attributes (note: text_weight = 1 - metadata_weight)
            item_history_weight: The weight given to the user history vs. the currently viewed item`
            text_embedding_method: Method that will embed the text attributes of the items.
            sentence_filtering_method: Method that will be used for filtering out non-informative sentences from the
                text attributes of the items
            recommendations_filtering_methods: A list of filtering methods that will be applied to each item id that is
                candidate for recommendations. Should take as input the id of the item and return True if the item
                should be kept, False otherwise.
            loggers: A list of loggers that will be used to log the recommendations created. Available: StdoutLogger,
                FileLogger, MongoLogger
            proc_numb: The number of processes to use for the calculation of the similarities.
            keep_embeddings: If True, the embeddings will be kept in the cache. If False, the embeddings will be deleted.
        """
        if recommender_id is None:
            # If it is none add the memory address to make the id unique
            recommender_id = "item_recommender_" + str(id(self))
            logger.warning(
                f"No recommender id provided. Using {recommender_id} as id. Recommender id is required "
                f"if persistence between runs is needed."
            )

        if cache_manager is None:
            logger.warning(
                "No cache manager provided. An in-memory cache manager will be used (no persistence)."
            )
            cache_manager = InMemoryCache()

        self.metadata_weight = metadata_weight
        self.item_history_weight = item_history_weight

        self.text_embeddings = TextEmbeddingsManager(
            cache_manager,
            text_embedding_method,
            sentence_filtering_method,
            recommender_id=recommender_id,
        )
        self.metadata_embeddings = MetadataEmbeddingsManager(
            cache_manager, recommender_id=recommender_id
        )
        self.keep_embeddings = keep_embeddings

        self.text_similarity = TextSimilarityManagerPerCorpus(
            cache_manager,
            recommender_id=recommender_id,
            proc_numb=proc_numb,
        )
        self.metadata_similarity = MetadataSimilarityManagerPerCorpus(
            cache_manager, recommender_id=recommender_id
        )

        self.filtering_methods = recommendations_filtering_methods
        self.loggers = loggers

    def initialise(self, items: Optional[List[Item]] = None) -> None:
        self.text_embeddings.initialise(items)
        self.metadata_embeddings.initialise(items)

        self.text_similarity.initialise(
            embeddings=self.text_embeddings.get_embeddings()
        )
        self.metadata_similarity.initialise(
            embeddings=self.metadata_embeddings.get_embeddings()
        )

        if not self.keep_embeddings:
            self.text_embeddings.delete_embeddings()
            self.metadata_embeddings.delete_embeddings()

    def update(self, items: List[Item]):
        self.text_embeddings.update(items)
        self.metadata_embeddings.update(items)

        self.text_similarity.update(embeddings=self.text_embeddings.get_embeddings())
        self.metadata_similarity.update(
            embeddings=self.metadata_embeddings.get_embeddings()
        )

    def add_item(self, item: Item) -> None:
        # Possibly will not be implemented
        pass

    def recommend(
        self, user_state: UserState, recs_num: int
    ) -> List[ItemRecommendation]:
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
