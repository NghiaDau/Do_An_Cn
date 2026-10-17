"""Cấu hình model embedding dùng chung (script nạp và API truy vấn)."""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

# gte-modernbert-base: context 8192 token (JD dài nhất ~4300 token), vector 768 chiều.
MODEL_NAME = "Alibaba-NLP/gte-modernbert-base"
MAX_SEQ_LENGTH = 8192

# gte không cần prefix cho cả tài liệu lẫn câu truy vấn.
DOC_PREFIX = ""
QUERY_PREFIX = ""


def load_model():
    model = SentenceTransformer(MODEL_NAME)
    model.max_seq_length = MAX_SEQ_LENGTH
    return model


@lru_cache(maxsize=1)
def get_model():
    """Model dùng chung cho API: chỉ nạp một lần, các lần sau dùng lại."""
    return load_model()


def embed_query(text: str) -> list[float]:
    return get_model().encode(QUERY_PREFIX + text, normalize_embeddings=True).tolist()
