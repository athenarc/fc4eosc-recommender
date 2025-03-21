from collections import Counter
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
from darelabdb.nlp_embeddings.embedding_methods.SBERTEmbedding import SBERTEmbedding
from darelabdb.nlp_embeddings.embedding_methods.TextEmbeddingMethodABC import (
    TextEmbeddingMethod,
)
from darelabdb.recs_similarity_based.components.embeddings.sentence_filtering.SentenceFilteringABC import (
    SentenceFiltering,
)
from darelabdb.recs_similarity_based.components.embeddings.text_embeddings import (
    TextEmbeddingsManager,
)
from darelabdb.recs_similarity_based.components.logging.LoggerABC import Logger
from darelabdb.recs_similarity_based.components.similarity.sdr_similarity import (
    calculate_sdr_similarities,
)
from darelabdb.recs_similarity_based.components.text_processing.TextProcessor import (
    TextProcessor,
    text_preprocessing,
)
from darelabdb.utils_cache.CacheABC import Cache
from darelabdb.utils_cache.InMemory import InMemoryCache
from darelabdb.utils_schemas.field_recommendation import FieldRecommendation
from darelabdb.utils_schemas.item import Item, item_id_type, metadata_attribute_type
from loguru import logger


class MetadataFieldRecommender:
    def __init__(
        self,
        field_values_getter: Callable[
            [str, List[item_id_type]], metadata_attribute_type
        ],
        recommender_id: str = None,
        cache_manager: Optional[Cache] = None,
        similarity_threshold: float = 0.3,
        considered_similar_items_threshold: int = 10,
        value_frequency_threshold: float = 0.3,
        text_embedding_method: Optional[TextEmbeddingMethod] = SBERTEmbedding(),
        sentence_filtering_method: Optional[SentenceFiltering] = None,
        loggers: Optional[List[Logger]] = None,
    ):
        """
        The metadata field recommender based on text similarity. Responsible for initialising the required managers
            (for the embeddings of the items) and providing recommendations of a metadata field values based on the given
            text attributes.

        Args:
            field_values_getter: A function that takes a list of item ids and returns the values that these items have
                in the requested field.
            recommender_id: An id to differentiate between other recommenders. Needs to be provided if persistence
                between runs is required.
            cache_manager: The cache manager to use. If None, an in-memory cache manager will be used.
                Possible values: None, InMemoryCache(), RedisCache()
            similarity_threshold: The minimum number of similarity for two text embeddings to be considered similar.
            considered_similar_items_threshold: The maximum number of items that will be considered as similar.
            value_frequency_threshold: The minimum frequency of a value in the similar items to be recommended.
            text_embedding_method: Method that will embed the text attributes of the items.
            sentence_filtering_method: Method that will be used for filtering out non-informative sentences from the
                text attributes of the items.
            loggers: A list of loggers that will be used to log the recommendations created. Available: StdoutLogger,
                FileLogger, MongoLogger
        """
        if recommender_id is None:
            # If it is none add the memory address to make the id unique
            recommender_id = "metadata_field_recommender_" + str(id(self))
            logger.warning(
                f"No recommender_id provided. Using {recommender_id} as recommender_id. Recommender id is "
                f"required if persistence between runs is needed."
            )

        if cache_manager is None:
            logger.warning(
                "No cache manager provided. An in-memory cache manager will be used (no persistence)."
            )
            cache_manager = InMemoryCache()

        self.similarity_threshold = similarity_threshold
        self.considered_similar_items_threshold = considered_similar_items_threshold
        self.value_frequency_threshold = value_frequency_threshold

        self.field_values_getter = field_values_getter

        self.text_processor = TextProcessor()
        self.sentence_filtering_method = sentence_filtering_method
        self.text_embeddings = TextEmbeddingsManager(
            cache_manager,
            text_embedding_method,
            sentence_filtering_method,
            recommender_id=recommender_id,
        )

        self.loggers = loggers

    def initialise(self, items: Optional[List[Item]]) -> None:
        self.text_embeddings.initialise(items)

    def update(self, items: List[Item]) -> None:
        self.text_embeddings.update(items)

    def _get_text_embeddings(
        self, text_attributes: Dict[str, str]
    ) -> List[List[float]]:
        """Returns the text embeddings of the given item"""
        sentences = text_preprocessing(
            text_attributes=text_attributes,
            text_processor=self.text_processor,
            sentence_filtering=self.sentence_filtering_method,
        )

        return self.text_embeddings.text_embedding_method.get_item_embedding(sentences)

    def _get_similar_items(
        self, text_embeddings: List[List[float]], similarity_threshold: float
    ) -> List[Any]:
        """
        Returns a list with the ids of the items with similar text in descending similarity order.

        Args:
            text_embeddings: A list with the sentence embeddings of an item
            similarity_threshold: The minimum similarity score for two texts to be considered similar
        """
        # Get the text embeddings of the catalog items
        items_embeddings = self.text_embeddings.get_embeddings()

        similarities = calculate_sdr_similarities(
            item_embedding=text_embeddings, items_embeddings=items_embeddings
        )

        # Connect the item ids with the similarities
        similarities = pd.Series(similarities, index=items_embeddings.index)

        # Sort similarities in descending order
        similarities = similarities.sort_values(ascending=False)

        similar_item_ids = similarities[
            similarities > similarity_threshold
        ].index.tolist()

        return similar_item_ids

    @staticmethod
    def _get_candidate_values(
        similar_items_values: List[str],
        considered_items_num: int,
        frequency_threshold: float,
    ) -> pd.Series:
        """
        Returns a dictionary with the candidates values and their frequencies

        Args:
            similar_items_values: A list with the field values of similar items
            considered_items_num: The number of items from which the values are taken
            frequency_threshold: The minimum frequency for a value to be considered candidate
        """
        # Get a dictionary with the values and their frequencies
        values_frequency = {
            value: counter / float(considered_items_num)
            for value, counter in dict(Counter(similar_items_values)).items()
        }

        # Filter out the values below the frequency threshold
        accepted_values = dict(
            filter(
                lambda elem: elem[1] >= frequency_threshold, values_frequency.items()
            )
        )

        return pd.Series(accepted_values)

    # TODO add check for field name
    def recommend(
        self,
        text_attributes: Dict[str, str],
        field_name: str,
        existing_values: List[str] = None,
        recs_num: int = 3,
    ) -> List[FieldRecommendation]:
        # Create a text embedding for the given text
        text_embeddings = self._get_text_embeddings(text_attributes)

        # Get the similar catalog items based on text
        items_with_similar_text = self._get_similar_items(
            text_embeddings, self.similarity_threshold
        )

        # Keep at most <considered_similar_items_threshold> similar items
        items_with_similar_text = items_with_similar_text[
            : self.considered_similar_items_threshold
        ]

        # Get the field values for all the items with similar text
        items_with_similar_text_field_values = self.field_values_getter(
            field_name, items_with_similar_text
        )

        # Remove existing values from the list
        if existing_values is not None:
            for existing_value in existing_values:
                if existing_value in items_with_similar_text_field_values:
                    items_with_similar_text_field_values.remove(existing_value)

        # Get the candidate values
        candidates = self._get_candidate_values(
            similar_items_values=items_with_similar_text_field_values,
            considered_items_num=len(items_with_similar_text),
            frequency_threshold=self.value_frequency_threshold,
        )

        # Order values by frequency
        candidates = candidates.sort_values(ascending=False)

        recommendations = [
            FieldRecommendation(value=value, score=score)
            for value, score in candidates[:recs_num].items()
        ]

        self._log(text_attributes=text_attributes, recommendations=recommendations)

        return recommendations

    def _log(self, text_attributes, recommendations: List[FieldRecommendation]):
        if self.loggers is not None:
            for log in self.loggers:
                log.log_field_recommendation(
                    text_attributes=text_attributes, recommendations=recommendations
                )
