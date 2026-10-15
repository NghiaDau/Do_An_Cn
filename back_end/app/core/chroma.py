"""Cấu hình ChromaDB dùng chung.

- Mặc định: PersistentClient, ghi thẳng vào thư mục back_end/chroma_db.
- Nếu đặt CHROMA_HOST (vd localhost): kết nối tới server Chroma qua HttpClient.
  Khi đó nhiều tiến trình (script nạp, FastAPI, UI) dùng chung một DB an toàn.
"""
import os
from pathlib import Path

import chromadb

CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_db"
COLLECTION = "job_descriptions"


def get_client():
    host = os.getenv("CHROMA_HOST")
    if host:
        return chromadb.HttpClient(host=host, port=int(os.getenv("CHROMA_PORT", "8000")))
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection():
    return get_client().get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def reset_collection():
    """Xóa hẳn collection (kể cả kích thước vector đã khóa) rồi tạo lại."""
    client = get_client()
    try:
        client.delete_collection(COLLECTION)
    except Exception:  # chưa tồn tại
        pass
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
