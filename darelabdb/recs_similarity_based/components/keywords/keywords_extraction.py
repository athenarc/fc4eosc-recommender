from typing import Dict, List, Union

import pytextrank
import spacy
from loguru import logger


class KeywordExtractor:
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        logger.debug("Initializing KeywordExtractor...")
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

        self.nlp.add_pipe("textrank")

    def retrieve_keywords(self, text: str) -> List[Dict[str, Union[str, float]]]:
        """
        This function returns the keywords extracted from the text with their scores
        Example returned value:
        ```
        [
            {'keyword': 'a really important dog', 'score': 0.18},
            {'keyword': 'This', 'score': 0.02}
        ]

        ```
        Args:
            text: The text from which the keywords will be extracted

        Returns:
            (List[Dict[str, Union[str, float]]]): The list of keywords with their scores
        """
        doc = self.nlp(text)
        keywords = []
        for phrase in doc._.phrases:
            keywords.append({"keyword": phrase.text, "score": phrase.rank})

        return keywords

    def sentencize_text(self, text: str) -> List[str]:
        """
        This function splits the text into sentences and returns them as a list
        Args:
            text: The text that will be split into sentences

        Returns:
            (List[str]): The list of sentences
        """
        doc = self.nlp(text)
        sentences = [sent.text for sent in doc.sents]

        return sentences
