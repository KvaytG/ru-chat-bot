import logging
import pathlib
import torch
from numpy import ndarray
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer

_logger = logging.getLogger(__name__)

_CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
_MODEL_PATH = _CURRENT_DIR.parent / "resources" / "rubert_tiny_onnx"
_MODEL_NAME = "cointegrated/rubert-tiny2"


def _get_model_and_tokenizer():
    onnx_file = _MODEL_PATH / "model.onnx"
    if not onnx_file.exists():
        _logger.info(f"ONNX model not found in {_MODEL_PATH}. I'm starting the download and conversion...")
        _MODEL_PATH.mkdir(parents=True, exist_ok=True)
        model = ORTModelForFeatureExtraction.from_pretrained(_MODEL_NAME, export=True)
        tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        model.save_pretrained(_MODEL_PATH)
        tokenizer.save_pretrained(_MODEL_PATH)
        _logger.info("The model has been successfully saved locally.")
    else:
        model = ORTModelForFeatureExtraction.from_pretrained(str(_MODEL_PATH), local_files_only=True)
        tokenizer = AutoTokenizer.from_pretrained(str(_MODEL_PATH), local_files_only=True)
    return model, tokenizer


_model, _tokenizer = _get_model_and_tokenizer()


def _pool_embeddings(last_hidden_state, attention_mask):
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    sum_embeddings = torch.sum(last_hidden_state * mask, dim=1)
    sum_mask = torch.clamp(mask.sum(1), min=1e-9)
    return sum_embeddings / sum_mask


def vectorize(data: str | list[str]) -> ndarray:
    is_single_string = isinstance(data, str)
    batch = [data] if is_single_string else data
    inputs = _tokenizer(
        batch,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt"
    )
    device = getattr(_model, "device", torch.device("cpu"))
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = _model(**inputs)
    embeddings = _pool_embeddings(outputs.last_hidden_state, inputs['attention_mask'])
    result = embeddings.cpu().numpy()
    return result[0] if is_single_string else result
