from fastapi import APIRouter, HTTPException, Query

from app.core.chroma import get_collection

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    keyword: str | None = Query(None, description="Lọc theo Primary Keyword, vd: Python"),
    full: bool = Query(False, description="Trả về toàn bộ Long Description"),
):
    col = get_collection()
    res = col.get(
        limit=limit,
        offset=offset,
        where={"keyword": keyword} if keyword else None,
        include=["metadatas", "documents"],
    )
    items = [
        {"id": i, **m, "description": d if full else d[:300]}
        for i, m, d in zip(res["ids"], res["metadatas"], res["documents"])
    ]
    return {"total": col.count(), "limit": limit, "offset": offset, "items": items}


@router.get("/{job_id}")
def get_job(job_id: str):
    res = get_collection().get(ids=[job_id], include=["metadatas", "documents"])
    if not res["ids"]:
        raise HTTPException(404, "Không tìm thấy JD")
    return {"id": job_id, **res["metadatas"][0], "description": res["documents"][0]}
