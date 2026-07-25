import json
import pathlib
import re
import dateparser
import pymorphy3
from dateparser.search import search_dates
from .nlp import nlp

_CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
_CITIES_PATH = str(_CURRENT_DIR.parent / "resources" / "cities.json")
_CITIES_SYNONYMS_PATH = str(_CURRENT_DIR.parent / "resources" / "cities-synonyms.json")

class NERManager:
    def __init__(self):
        self._morph = pymorphy3.MorphAnalyzer()
        self._load_patterns()

    @staticmethod
    def _load_patterns():
        patterns = []
        with open(_CITIES_PATH, "r", encoding="utf-8") as f:
            cities_data = json.load(f)
            for city in cities_data.get("cities", []):
                patterns.append({"label": "LOC", "pattern": city, "id": city})
        with open(_CITIES_SYNONYMS_PATH, "r", encoding="utf-8") as f:
            synonyms_data = json.load(f)
            for item in synonyms_data:
                main_city = item["city"]
                for syn in item["synonyms"]:
                    if syn["type"] == "LEMMA":
                        pattern_val = [{"LEMMA": syn["synonym"].lower()}]
                    else:
                        pattern_val = syn["synonym"]
                    patterns.append({
                        "label": "LOC",
                        "pattern": pattern_val,
                        "id": main_city
                    })
        if patterns:
            nlp.ruler.add_patterns(patterns)

    @staticmethod
    def _get_cities(text: str) -> list[dict]:
        doc = nlp.get(text)
        cities = []
        for ent in doc.ents:
            if ent.label_ == "LOC":
                name = ent.ent_id_ if ent.ent_id_ else ent.lemma_.title()
                cities.append({"name": name, "pos": ent.start_char})
        return cities

    @staticmethod
    def _get_dates(text: str) -> list[dict]:
        settings = {'PREFER_DATES_FROM': 'future', 'DATE_ORDER': 'DMY'}
        results = search_dates(text, languages=['ru'], settings=settings) or []
        found_dates = []
        for t_match, dt_obj in results:
            found_dates.append({
                "text": t_match,
                "date": dt_obj,
                "pos": text.find(t_match)
            })
        date_pattern = r'\b\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4}\b'
        for match in re.finditer(date_pattern, text):
            if not any(match.group() in d['text'] for d in found_dates):
                parsed = dateparser.parse(match.group(), settings={'DATE_ORDER': 'DMY'})
                if parsed:
                    found_dates.append({"text": match.group(), "date": parsed, "pos": match.start()})
        return found_dates

    def analyze(self, text: str) -> list[dict]:
        cities = self._get_cities(text)
        dates = self._get_dates(text)
        seen_pos = set()
        unique_cities = []
        for c in cities:
            position = c.get('pos')
            if position not in seen_pos:
                unique_cities.append(c)
                seen_pos.add(position)
        itinerary = []
        if unique_cities:
            for city in unique_cities:
                res_item = {"city": city['name'], "date": None}
                if dates:
                    closest_date = min(dates, key=lambda d: abs(d['pos'] - city['pos']))
                    res_item["date"] = closest_date['date']
                itinerary.append(res_item)
        elif dates:
            first_date = dates[0]['date']
            itinerary.append({"city": None, "date": first_date})
        return itinerary

    @staticmethod
    def get_subject(text: str) -> str:
        doc = nlp.get(text)
        if doc.ents:
            return max(doc.ents, key=lambda e: len(e.text)).text
        for token in doc:
            if token.pos_ in ("NOUN", "PROPN"):
                phrase = [t for t in token.children if t.pos_ in ("ADJ", "NUM", "DET")] + [token]
                phrase.sort(key=lambda x: x.i)
                return " ".join([t.text for t in phrase])
        return text


ner_manager = NERManager()
