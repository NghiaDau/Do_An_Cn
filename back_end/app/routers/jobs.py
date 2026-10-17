from fastapi import APIRouter, HTTPException, Query

from app.core.chroma import get_collection
from app.core.embedding import embed_query

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    keyword: str | None = Query(None, description="Lọc theo Primary Keyword, vd: Python"),
):
    col = get_collection()
    res = col.get(
        limit=limit,
        offset=offset,
        where={"keyword": keyword} if keyword else None,
        include=["metadatas", "documents"],
    )
    items = [
        {"id": i, **m, "description": d}
        for i, m, d in zip(res["ids"], res["metadatas"], res["documents"])
    ]
    return {"total": col.count(), "limit": limit, "offset": offset, "items": items}


@router.get("/search")
def search_jobs(
    q: str = Query(..., min_length=1, description="Câu truy vấn tự nhiên, vd: backend python developer"),
    limit: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, description="Lọc đúng Primary Keyword, vd: Python"),
    company: str | None = Query(None, description="Lọc đúng tên công ty"),
    min_exp: int | None = Query(None, ge=0, description="Số năm kinh nghiệm tối thiểu"),
    max_exp: int | None = Query(None, ge=0, description="Số năm kinh nghiệm tối đa"),
    min_english: int | None = Query(None, ge=1, le=5, description="Mức tiếng Anh tối thiểu (1=basic ... 5=fluent)"),
    max_english: int | None = Query(None, ge=1, le=5, description="Mức tiếng Anh tối đa"),
):
    """Hybrid search: tìm theo ngữ nghĩa (vector) kết hợp lọc metadata trong cùng một lần truy vấn."""
    conds = []
    if keyword:
        conds.append({"keyword": keyword})
    if company:
        conds.append({"company": company})
    if min_exp is not None:
        conds.append({"exp_years": {"$gte": min_exp}})
    if max_exp is not None:
        conds.append({"exp_years": {"$lte": max_exp}})
    if min_english is not None:
        conds.append({"english_level_num": {"$gte": min_english}})
    if max_english is not None:
        conds.append({"english_level_num": {"$lte": max_english}})
    where = None if not conds else conds[0] if len(conds) == 1 else {"$and": conds}

    res = get_collection().query(
        query_embeddings=[embed_query(q)],
        n_results=limit,
        where=where,
        include=["metadatas", "documents", "distances"],
    )
    items = [
        {"id": i, "score": round(1 - dist, 4), **m, "description": d}
        for i, m, d, dist in zip(res["ids"][0], res["metadatas"][0], res["documents"][0], res["distances"][0])
    ]
    return {"query": q, "count": len(items), "items": items}


@router.get("/{job_id}")
def get_job(job_id: str):
    res = get_collection().get(ids=[job_id], include=["metadatas", "documents"])
    if not res["ids"]:
        raise HTTPException(404, "Không tìm thấy JD")
    return {"id": job_id, **res["metadatas"][0], "description": res["documents"][0]}
