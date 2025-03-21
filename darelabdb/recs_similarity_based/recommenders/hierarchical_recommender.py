from typing import Callable, Dict, Optional

from darelabdb.nlp_embeddings.embedding_methods.SBERTEmbedding import SBERTEmbedding
from darelabdb.nlp_embeddings.embedding_methods.TextEmbeddingMethodABC import (
    TextEmbeddingMethod,
)
from darelabdb.recs_similarity_based import ItemRecommender
from darelabdb.recs_similarity_based.components.clustering.kmeans_with_tf_idf import (
    kmeans_with_tf_idf_clustering,
)
from darelabdb.recs_similarity_based.components.embeddings.sentence_filtering.SentenceFilteringABC import (
    SentenceFiltering,
)
from darelabdb.recs_similarity_based.components.logging.LoggerABC import Logger
from darelabdb.utils_cache.CacheABC import Cache
from darelabdb.utils_schemas.item import Item, item_id_type
from darelabdb.utils_schemas.item_recommendation import ItemRecommendation
from darelabdb.utils_schemas.user_state import UserState
from loguru import logger

# TODO items in the user history from different clusters!
# TODO case when recs_num > cluster_items_num


class HierarchicalRecommender:
    def __init__(
        self,
        recommender_id: str = None,
        cache_manager: Optional[Cache] = None,
        metadata_weight: Optional[float] = 0.25,
        # item_history_weight: Optional[float] = 0.25,
        text_embedding_method: Optional[TextEmbeddingMethod] = SBERTEmbedding(),
        sentence_filtering_method: Optional[SentenceFiltering] = None,
        recommendations_filtering_methods: Optional[list[Callable]] = None,
        loggers: Optional[list[Logger]] = None,
        proc_numb: Optional[int] = 1,
        clusters_num: Optional[int] = 10,
        tf_idf_vectorizer_settings: Dict = None,
        keep_embeddings: Optional[bool] = True,
    ):
        """
        The item-item recommender based on similarity. Responsible for initialising the required managers
        (for the embeddings and the similarities of the items) and providing recommendations based on the user state.

        Args:
            recommender_id: An id to differentiate between other recommenders. Needs to be provided if persistence
                between runs is required. For each cluster-recommender the recommender id will be used as a prefix
                followed by the id of the cluster.
            cache_manager: The cache manager to use. If None, an in-memory cache manager will be used.
                Possible values: None, InMemoryCache(), RedisCache()
            metadata_weight: The weight given to metadata vs. text attributes (note: text_weight = 1 - metadata_weight)
            text_embedding_method: Method that will embed the text attributes of the items.
            sentence_filtering_method: Method that will be used for filtering out non-informative sentences from the
                text attributes of the items
            recommendations_filtering_methods: A list of filtering methods that will be applied to each item id that is
                candidate for recommendations. Should take as input the id of the item and return True if the item
                should be kept, False otherwise.
            loggers: A list of loggers that will be used to log the recommendations created. Available: StdoutLogger,
                FileLogger, MongoLogger
            proc_numb: The number of processes to use for the calculation of the similarities.
            clusters_num: The number of item clusters.
            tf_idf_vectorizer_settings: A dictionary holding the parameters for the tf_idf vectorizer used in nearest
                neighbors. Parameters: item_vector_dimension, l2_normalize, max_df, min_df, max_features
            keep_embeddings: If True, the embeddings will be kept in the cache. If False, the embeddings will be deleted.
        """

        self.clusters_num = clusters_num
        self.tf_idf_vectorizer_settings = (
            tf_idf_vectorizer_settings if tf_idf_vectorizer_settings else {}
        )

        if recommender_id is None:
            # If it is none add the memory address to make the id unique
            recommender_id = "item_recommender_" + str(id(self))
            logger.warning(
                f"No recommender id provided. Using {recommender_id} as id. Recommender id is required "
                f"if persistence between runs is needed."
            )
        self.recommender_id_prefix = recommender_id

        self.item_recommender_arguments = {
            "cache_manager": cache_manager,
            "metadata_weight": metadata_weight,
            "item_history_weight": 0,
            "text_embedding_method": text_embedding_method,
            "sentence_filtering_method": sentence_filtering_method,
            "recommendations_filtering_methods": recommendations_filtering_methods,
            "loggers": loggers,
            "proc_numb": proc_numb,
            "keep_embeddings": keep_embeddings,
        }

        self.recommender_per_cluster = None
        self.items_recommender_mapping = None

        # All the structures required for finding the cluster of a new item
        self.clustering_structures = {}

    def _create_item_clusters(self, items: list[Item]) -> list[list[Item]]:
        """
        Creates clusters of the given items.
        Args:
            items (list[Item]): A list with the items to be clustered.

        Returns (list[list[Item]]):
            A list with the items in each cluster.

        """

        logger.info(
            f"Creating the item clusters of {self.recommender_id_prefix} recommender..."
        )

        clusters, vectorizer, pca, kmeans = kmeans_with_tf_idf_clustering(
            items=items,
            clusters_num=self.clusters_num,
            **self.tf_idf_vectorizer_settings,
        )

        # Store the structures required for clustering a new item
        self.clustering_structures = {
            "vectorizer": vectorizer,
            "pca": pca,
            "kmeans": kmeans,
        }

        return clusters

    def _create_item_recommender_per_cluster(
        self, clusters: list[list[Item]]
    ) -> (dict[str, ItemRecommender], dict[item_id_type, str]):
        recommenders = {}
        items_recommender_mapping = {}
        for enum, cluster in enumerate(clusters):
            # Create an item recommender
            cluster_recommender_id = f"{self.recommender_id_prefix}_cluster_{enum}"

            logger.info(f"Initializing {cluster_recommender_id} cluster-recommender...")

            cluster_recommender = ItemRecommender(
                recommender_id=cluster_recommender_id, **self.item_recommender_arguments
            )
            # Initialize the recommender
            cluster_recommender.initialise(cluster)

            items_recommender_mapping.update(
                {item.item_id: cluster_recommender_id for item in cluster}
            )
            recommenders[cluster_recommender_id] = cluster_recommender

            logger.info(
                f"{cluster_recommender_id} cluster-recommender was successfully initialized!"
            )

        return recommenders, items_recommender_mapping

    def _get_item_recommender(self, item_id) -> ItemRecommender:
        return self.recommender_per_cluster[self.items_recommender_mapping[item_id]]

    def initialise(self, items: list[Item]) -> None:
        # Divide items into clusters
        clusters = self._create_item_clusters(items)

        # Create an item recommender for every cluster
        (
            self.recommender_per_cluster,
            self.items_recommender_mapping,
        ) = self._create_item_recommender_per_cluster(clusters)

    def update(self, items: list[Item]) -> None:
        pass

    def recommend(
        self, user_state: UserState, recs_num: int
    ) -> list[ItemRecommendation]:
        recommender = self._get_item_recommender(user_state.viewed_item_id)

        return recommender.recommend(user_state=user_state, recs_num=recs_num)
