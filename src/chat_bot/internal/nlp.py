import spacy
from spacy.pipeline import EntityRuler
from typing import cast


class NLP:
    def __init__(self):
        spacy_model_name = "ru_core_news_sm"
        try:
            self._nlp = spacy.load(spacy_model_name)
        except OSError:
            spacy.cli.download(spacy_model_name)
            self._nlp = spacy.load(spacy_model_name)
        self.ruler = cast(EntityRuler, self._nlp.add_pipe("entity_ruler", before="ner"))

    def get(self, text: str):
        return self._nlp(text)

nlp = NLP()
