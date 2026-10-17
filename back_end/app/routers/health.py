from fastapi import APIRouter, HTTPException

from app.core.chroma import COLLECTION, get_collection

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    try:
        total = get_collection().count()
    except Exception as e:
        raise HTTPException(503, f"Không kết nối được ChromaDB: {e}")
    return {"status": "ok", "collection": COLLECTION, "total_jobs": total}
