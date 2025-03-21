from typing import Dict, List

import spacy
from darelabdb.recs_similarity_based.components.embeddings.sentence_filtering.SentenceFilteringABC import (
    SentenceFiltering,
)
from loguru import logger

ACCEPTED_ENTITIES = {
    "PERSON",
    "FAC",
    "ORG",
    "PRODUCT",
    "EVENT",
    "CARDINAL",
    "ORDINAL",
    "QUANTITY",
}


class NerSentenceFiltering(SentenceFiltering):
    def __init__(self, text_attributes: List[str], spacy_model: str = "en_core_web_sm"):
        """
        This class is responsible for filtering out non-informative sentences from the text attributes of the items.
        We use entities extracted from the text attributes to filter out the sentences that do not contain any.

        ENTITY_TYPES = {'PERSON', 'FAC', 'ORG', 'PRODUCT', 'EVENT', 'CARDINAL', 'ORDINAL', 'QUANTITY'}

        Args:
            text_attributes (List[str]): The text attributes that sentence filtering will be applied to
                (i.e. ["description"])
            spacy_model (str): The spacy model to use for entity extraction (the package comes with "en_core_web_sm",
                any other package must be installed by the user)
        """
        logger.debug("Initializing NER based sentence filtering...")
        try:
            # Spacy does not allow for automatically downloading missing models
            # The use must manually install it via pip
            self.nlp = spacy.load(spacy_model)
        except OSError:
            logger.debug(f"Spacy model {spacy_model} not found.")
            raise OSError(
                f"Spacy model {spacy_model} not found. "
                f"Please install it via pip or your preferred package manager."
            )
        self.text_attributes = text_attributes

    def filter_text_attributes(self, item_texts: Dict[str, str]) -> Dict[str, str]:
        for text_attribute in self.text_attributes:
            if text_attribute not in item_texts:
                raise ValueError(
                    f"Text attribute {text_attribute} not found in item_texts. "
                    f"Available values: {item_texts.keys()}"
                )

            doc = self.nlp(item_texts[text_attribute])
            sentences = [sent.text for sent in doc.sents]
            item_texts[text_attribute] = " ".join(self.filter(sentences))

        return item_texts

    def filter(self, sentences: List[str]) -> List[str]:
        entities = self.nlp(" ".join(sentences)).ents
        accepted_entities_text = {
            entity.text for entity in entities if entity.label_ in ACCEPTED_ENTITIES
        }

        selected_sentences = [
            sentence
            for sentence in sentences
            if self._check_entity_existence(accepted_entities_text, sentence)
        ]

        return selected_sentences

    @staticmethod
    def _check_entity_existence(entities, sentence):
        for entity in entities:
            if entity in sentence:
                return True
        return False
