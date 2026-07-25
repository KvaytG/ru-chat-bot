import asyncio
import json
import logging
import os
import pathlib
import aiohttp
import torch
import torch.nn.functional as F
from .model import IntentModel
from .phrases import phrase_manager
from .text_cleaner import text_cleaner
from .vectorizer import vectorize

_CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
_MODEL_PATH = str(_CURRENT_DIR.parent / "resources" / "model.pt")
_PARAMS_PATH = str(_CURRENT_DIR.parent / "resources" / "params.json")
_FAST_INTENTS_PATH = str(_CURRENT_DIR.parent / "resources" / "fast-intents.json")

_logger = logging.getLogger(__name__)

_FALLBACK_ID = -1


class NLUManager:
    def __init__(self, input_dim: int = 312):
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._mapping = self._load_mapping()
        self._tag_to_id = {tag: idx for idx, tag in self._mapping.items()}
        self._unknown_id = self._tag_to_id.get("unknown", 0)
        self._temperature = 1.0
        self._threshold = 0.5
        self._load_params()
        self._fast_lookup = {}
        self._load_fast_intents()
        self._model = IntentModel(input_dim, len(self._mapping)).to(self._device)
        self._load_model()

    @staticmethod
    def _load_mapping() -> dict[int, str]:
        return {
            0: 'unknown',
            1: 'origin',
            2: 'time',
            3: 'date',
            4: 'weather',
            5: 'news',
            6: 'wiki'
        }

    def _load_model(self):
        if os.path.exists(_MODEL_PATH):
            try:
                self._model.load_state_dict(torch.load(_MODEL_PATH, map_location=self._device))
                self._model.eval()
                _logger.info(f"Модель загружена. T={self._temperature:.2f}, Threshold={self._threshold:.2f}")
            except Exception as e:
                _logger.error(f"Не удалось загрузить веса модели: {e}")
        else:
            _logger.warning("Файл модели не найден. Работа только на fast-intents.")

    def _load_params(self):
        if not os.path.exists(_PARAMS_PATH):
            _logger.warning(f"Файл {_PARAMS_PATH} не найден. Используются параметры по умолчанию.")
            return
        try:
            with open(_PARAMS_PATH, encoding="utf-8") as f:
                params = json.load(f)
            self._temperature = float(params.get("temperature", self._temperature))
            self._threshold = float(params.get("threshold", self._threshold))
            _logger.debug(f"Загружены параметры: T={self._temperature:.2f}, Threshold={self._threshold:.2f}")
        except Exception as e:
            _logger.error(f"Ошибка при чтении params.json: {e}")

    def _load_fast_intents(self):
        if not os.path.exists(_FAST_INTENTS_PATH):
            _logger.warning(f"Файл {_FAST_INTENTS_PATH} не найден. Быстрый поиск отключен.")
            return
        try:
            with open(_FAST_INTENTS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            count = 0
            for tag, patterns in data.items():
                if tag not in self._tag_to_id:
                    _logger.warning(f"Тег '{tag}' из fast-intents не найден в маппинге. Пропускаем.")
                    continue
                intent_id = self._tag_to_id[tag]
                for phrase in patterns:
                    key = text_cleaner.clean(phrase)
                    if key and key not in self._fast_lookup:
                        self._fast_lookup[key] = _FALLBACK_ID if intent_id == self._unknown_id else intent_id
                        count += 1
            _logger.info(f"Загружено {count} быстрых правил из fast-intents.json")
        except Exception as e:
            _logger.error(f"Ошибка при загрузке fast-intents.json: {e}")

    def get_intent(self, message: str) -> tuple[int, float]:
        clean_msg = text_cleaner.clean(message)
        if not clean_msg:
            return _FALLBACK_ID, 1.0
        if clean_msg in self._fast_lookup:
            intent_id = self._fast_lookup[clean_msg]
            tag_name = self._mapping.get(intent_id, "fallback")
            _logger.debug(f"[FAST MATCH] Совпадение: '{clean_msg}' -> {tag_name}")
            return intent_id, 1.0
        vec = vectorize([clean_msg]) if isinstance(clean_msg, str) else vectorize(clean_msg)
        if vec.ndim == 1:
            vec = vec.reshape(1, -1)
        vec_tensor = torch.from_numpy(vec).float().to(self._device)
        with torch.no_grad():
            logits = self._model(vec_tensor)
            scaled_logits = logits / self._temperature
            probs = F.softmax(scaled_logits, dim=1)
        confidence, intent_tensor = torch.max(probs, dim=1)
        conf_value = confidence.item()
        intent_id = intent_tensor.item()
        if intent_id == self._unknown_id or conf_value < self._threshold:
            return _FALLBACK_ID, conf_value
        return intent_id, conf_value

    async def get_answer(self, intent_id: int, user_id: int, text: str,
                         http_session: aiohttp.ClientSession) -> str | None:
        if intent_id == _FALLBACK_ID:
            return None
        tag = self._mapping.get(intent_id)
        if not tag:
            return None
        response = phrase_manager.get(tag, user_id, text=text, http_session=http_session)
        if asyncio.iscoroutine(response):
            return await response
        return response


nlu_manager = NLUManager()
