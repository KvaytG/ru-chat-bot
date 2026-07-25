import re
from .nlp import nlp
from .preprocess import preprocess_text


class TextCleaner:
    def __init__(self):
        self._STOP_WORDS = {
            "ок", "окей", "слушай", "ну", "вот", "так", "как", "бы", "же", "ли", "то",
            "кстати", "короче", "значит", "тип", "типо", "собственно", "ладно", "давай",
            "пожалуйста", "срочно", "быстро", "немедленно", "вообще"
        }
        self._STOP_PHRASES = [
            r"будь добр[ао]?",
            r"если не сложно",
            r"если тебе не сложно",
            r"короче говоря"
        ]
        self._STOP_WORDS_PATTERN = re.compile(
            r"\b(" + "|".join(list(self._STOP_WORDS) + self._STOP_PHRASES) + r")\b",
            re.IGNORECASE
        )
        self._SUFFIX_PARTICLE_PATTERN = re.compile(r"-(то|ка)\b", re.IGNORECASE)
        self._STOP_LEMMAS = {
            "хотеть", "попросить", "попробовать", "уметь", "суметь", "мочь", "смочь", "становиться", "стать"
        }

    def clean(self, text: str) -> str:
        if not text:
            return ""
        text = preprocess_text(text)
        text = self._SUFFIX_PARTICLE_PATTERN.sub("", text)
        text = self._STOP_WORDS_PATTERN.sub("", text)
        doc = nlp.get(text)
        cleaned_tokens = []
        for token in doc:
            if token.is_punct or token.is_space:
                continue
            lemma = token.lemma_.lower()
            if lemma in self._STOP_LEMMAS and token.pos_ in ("VERB", "AUX"):
                continue
            cleaned_tokens.append(token.text)
        return " ".join(cleaned_tokens).strip()


text_cleaner = TextCleaner()
