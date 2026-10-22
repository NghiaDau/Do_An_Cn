import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.cv_pdf import PdfError, extract_text
from app.core.cv_profile import CandidateProfile, LlmNotConfigured, parse_cv

log = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/cv", tags=["cv"])

MAX_PDF_BYTES = 10 * 1024 * 1024


@router.post("/parse", response_model=CandidateProfile)
def parse_cv_pdf(file: UploadFile = File(..., description="CV dạng PDF (tối đa 10MB)")):
    """Đọc text từ PDF rồi nhờ LLM chuẩn hóa thành CandidateProfile (cùng định dạng metadata của JD)."""
    data = file.file.read(MAX_PDF_BYTES + 1)
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(413, "File PDF vượt quá 10MB")
    try:
        text = extract_text(data)
    except PdfError as e:
        raise HTTPException(422, str(e))

    try:
        return parse_cv(text)
    except LlmNotConfigured as e:
        raise HTTPException(503, str(e))
    except Exception:
        log.exception("Lỗi khi gọi LLM để phân tích CV")
        raise HTTPException(502, "Không phân tích được CV bằng LLM, thử lại sau")
