import re
from typing import Dict, List

import spacy
from darelabdb.recs_similarity_based.components.embeddings.sentence_filtering.SentenceFilteringABC import (
    SentenceFiltering,
)
from nltk.stem.porter import PorterStemmer


class TextProcessor:
    def __init__(self, sentence_filtering: SentenceFiltering = None):
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.stemmer = PorterStemmer()

    @staticmethod
    def clean_text(text: str, extra_rules: dict[str, str] = None):
        """
        Args:
            text (str)
            extra_rules (dict[str, str]): The additional replacements that will be applied to clean the text

        """
        text = re.sub("<[^<]+?>", "", text)

        text = text.replace("\n", ".")
        text = text.replace("**", "")

        if extra_rules is not None:
            for old, new in extra_rules.items():
                text = text.replace(old, new)

        return text

    def normalization(self, texts: list[str]):
        normalized_texts = []
        for text in texts:
            # Lowercase
            text = text.lower()

            doc = self.spacy_nlp(text)

            # Remove stopwords and punctuation
            preprocessed_words = []
            for word in doc:
                # Remove stopwords and punctuation
                if not word.is_stop and not word.is_punct:
                    # Lemmatize
                    preprocessed_words.append(word.lemma_)

            normalized_texts.append(" ".join(preprocessed_words))

        return normalized_texts

    def stemming(self, text):
        return " ".join(
            [self.stemmer.stem(token.text) for token in self.spacy_nlp(text)]
        )

    def lemmatization(self, text):
        return " ".join([token.lemma_ for token in self.spacy_nlp(text)])

    def sentencizer(self, text):
        return [str(sent) for sent in self.spacy_nlp(text).sents]

    def remove_stopwords(self, text):
        return " ".join(
            [token.text for token in self.spacy_nlp(text) if not token.is_stop]
        )

    @staticmethod
    def contains_english_char(text: str) -> bool:
        return re.search("[a-zA-Z]", text) is not None

    # def filter_sentences(self, ):
    #     if self.sentence_filtering is not None:
    # #     text_attributes = self.sentence_filtering_method.filter_text_attributes(text_attributes)


def text_preprocessing(
    text_attributes: Dict[str, str],
    text_processor: TextProcessor,
    sentence_filtering: SentenceFiltering = None,
) -> List[str]:
    # Step 1: Clean text
    for key, text in text_attributes.items():
        text_attributes[key] = text_processor.clean_text(
            text, extra_rules={"..": ".", "-": " ", "*": ""}
        )

    # Step 2: Filter out non-informative sentences
    if sentence_filtering is not None:
        text_attributes = sentence_filtering.filter_text_attributes(text_attributes)

    # Step 3: Concatenate all the text attributes and split them into sentences
    text = " ".join(text_attributes.values())
    sentences = text_processor.sentencizer(text)

    # Filter out sentences that do not contain any characters (needed for most language models)
    sentences = [
        sentence
        for sentence in sentences
        if text_processor.contains_english_char(sentence)
    ]

    return sentences
