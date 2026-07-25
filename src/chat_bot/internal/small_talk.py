import json
import faiss
import pathlib
import logging
from .vectorizer import vectorize

_logger = logging.getLogger(__name__)

_CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
_INDEX_PATH = str(_CURRENT_DIR.parent / "resources" / "dssm-index.faiss")
_ANSWERS_PATH = str(_CURRENT_DIR.parent / "resources" / "dssm-answers.json")


class SmallTalk:
    def __init__(self):
        try:
            self._index = faiss.read_index(_INDEX_PATH)
            with open(_ANSWERS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.answers = {int(k): v for k, v in data.items()}
            _logger.info("FAISS индекс и база ответов успешно загружены")
        except Exception as e:
            _logger.error(f"Ошибка при инициализации SmallTalk: {e}")
            raise

    def get_answer(self, query: str) -> tuple[str, float]:
        vec = vectorize(query).astype('float32').reshape(1, -1)
        distances, indices = self._index.search(vec, 5)
        best_idx = indices[0][0]
        score = float(distances[0][0])
        final_answer = self.answers.get(best_idx)
        _logger.debug(f"SmallTalk поиск: query='{query[:30]}', best_score={score:.4f}")
        return final_answer, score


talk_manager = SmallTalk()
