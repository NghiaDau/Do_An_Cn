"""Đọc text từ file PDF bằng PyMuPDF."""
import pymupdf


class PdfError(ValueError):
    """File không phải PDF hợp lệ, hoặc không có text để đọc."""


def extract_text(data: bytes) -> str:
    """Trả về toàn bộ text của PDF (các trang nối nhau theo thứ tự đọc)."""
    if not data.lstrip()[:5].startswith(b"%PDF"):
        raise PdfError("File không phải PDF")
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as e:  # file hỏng
        raise PdfError(f"Không mở được PDF: {e}") from e

    with doc:
        if doc.needs_pass:
            raise PdfError("PDF có đặt mật khẩu")
        pages = [page.get_text("text", sort=True) for page in doc]

    text = "\n".join(p.strip() for p in pages if p.strip())
    if not text:
        raise PdfError("PDF không có text (có thể là bản scan/ảnh, cần OCR)")
    return text
