from typing import Dict, List

from darelabdb.recs_similarity_based.components.embeddings.sentence_filtering.SentenceFilteringABC import (
    SentenceFiltering,
)
from darelabdb.recs_similarity_based.components.keywords.keywords_extraction import (
    KeywordExtractor,
)
from loguru import logger


class KeywordSentenceFiltering(SentenceFiltering):
    def __init__(
        self,
        text_attributes: List[str],
        spacy_model: str = "en_core_web_sm",
        top_n: int = 4,
    ):
        """
        This class is responsible for filtering out non-informative sentences from the text attributes of the items.
        We use the top N keywords extracted from the text attributes to filter out the sentences that do not contain
        any.

        Args:
            text_attributes (List[str]): The text attributes that sentence filtering will be applied to
                (i.e. ["description"])
            spacy_model (str): The spacy model to use for keyword extraction (the package comes with "en_core_web_sm",
                any other package must be installed by the user)
            top_n (int): The number of top keywords to use for filtering
        """
        logger.debug("Initializing Keyword based sentence filtering...")
        self.top_n = top_n
        self.keyword_extractor = KeywordExtractor(spacy_model=spacy_model)
        self.text_attributes = text_attributes

    def filter_text_attributes(self, item_texts: Dict[str, str]) -> Dict[str, str]:
        for text_attribute in self.text_attributes:
            if text_attribute not in item_texts:
                raise ValueError(
                    f"Text attribute {text_attribute} not found in item_texts. "
                    f"Available values: {item_texts.keys()}"
                )

            sentences = self.keyword_extractor.sentencize_text(
                item_texts[text_attribute]
            )
            item_texts[text_attribute] = " ".join(self.filter(sentences))

        return item_texts

    def filter(self, sentences: List[str]) -> List[str]:
        sorted_keywords = sorted(
            self.keyword_extractor.retrieve_keywords(" ".join(sentences)),
            key=lambda x: x["score"],
            reverse=True,
        )
        selected_keywords = [
            keyword["keyword"] for keyword in sorted_keywords[: self.top_n]
        ]

        return [
            sentence
            for sentence in sentences
            if self._check_keyword_existence(selected_keywords, sentence)
        ]

    @staticmethod
    def _check_keyword_existence(keywords, sentence):
        for keyword in keywords:
            if keyword in sentence:
                return True
        return False
