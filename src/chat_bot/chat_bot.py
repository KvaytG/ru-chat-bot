import asyncio
import logging
import aiohttp
from toxicity_detector import ToxicityDetector
from .internal.small_talk import talk_manager
from .internal.nlu import nlu_manager
from .internal.validator import is_valid_text

_logger = logging.getLogger(__name__)


class ChatBot:
    def __init__(self, http_session: aiohttp.ClientSession, dssm_threshold: float = 0.0):
        self._http_session = http_session
        self._dssm_threshold = dssm_threshold
        self._toxicity_detector = ToxicityDetector()
        _logger.info("ChatBot инициализирован.")

    async def handle_message(self, user_id: int, user_input: str) -> str:
        _logger.info(f"Получено сообщение от {user_id}: {user_input}")
        if not is_valid_text(user_input):
            _logger.info(f"Пользователь {user_id} пишет не по-русски.")
            return "I'm sorry, but I only support the Russian language so far."
        prediction = await asyncio.to_thread(self._toxicity_detector.predict, user_input)
        if prediction['is_toxic']:
            _logger.info(f"Обнаружена токсичность в сообщении от {user_id} (score: {prediction['score']}).")
            return "Не уверен, что могу помочь вам."
        intent_id, confidence = await asyncio.to_thread(nlu_manager.get_intent, user_input)
        response = await nlu_manager.get_answer(intent_id, user_id, user_input, self._http_session)
        if response:
            _logger.info(f"Найден ответ для {user_id} (intent_id: {intent_id}, confidence: {confidence}).")
            return response
        response, _ = await asyncio.to_thread(talk_manager.get_answer, user_input)
        _logger.info(f"Найден ответ через SmallTalk для {user_id}: {response}")
        return response
