from abc import ABC, abstractmethod
from typing import Dict, List


class SentenceFiltering(ABC):
    @abstractmethod
    def filter_text_attributes(self, item_texts: Dict[str, str]) -> Dict[str, str]:
        """
        Filter out the non-informative sentences from the text attributes of the items.

        Args:
            item_texts: The text attributes of the item (as defined in the Item model)

        Returns:
            (Dict[str, str]): The filtered text attributes (has the same structure as the input item texts)
        """
        pass

    @abstractmethod
    def filter(self, sentences: List[str]) -> List[str]:
        """
        Given a list of sentences return the ones that are the most valuable ignoring "filler" ones.
        Args:
            sentences: A list of sentences
        Returns:
            (List[str]): The most informative sentences
        """
        pass
