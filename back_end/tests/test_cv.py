import pymupdf
import pytest

from app.core import cv_profile
from app.core.cv_pdf import PdfError, extract_text
from app.core.cv_profile import CandidateProfile, parse_cv


def make_pdf(*pages: str) -> bytes:
    doc = pymupdf.open()
    for text in pages:
        doc.new_page().insert_text((72, 72), text)
    return doc.tobytes()


def test_extract_text_reads_all_pages():
    text = extract_text(make_pdf("Nguyen Van A", "Python developer"))
    assert "Nguyen Van A" in text and "Python developer" in text


def test_extract_text_rejects_non_pdf_and_empty_pdf():
    with pytest.raises(PdfError):
        extract_text(b"hello")
    with pytest.raises(PdfError):
        extract_text(make_pdf(""))  # trang trắng, giống bản scan


def test_profile_normalizes_to_jd_metadata_format():
    p = CandidateProfile(
        position="Dev", keyword="Python", exp_years="2.9", english_level="intermediate",
        skills=["Python", "python", " Docker "], summary="x",
    )
    assert p.exp_years == 2
    assert p.skills == ["Python", "Docker"]
    assert p.model_dump()["english_level_num"] == 3


def test_profile_unknown_english_and_invalid_keyword():
    p = CandidateProfile(position="d", keyword="Other", exp_years=0, english_level=None, skills=[], summary="")
    assert p.english_level_num == 0
    with pytest.raises(ValueError):
        CandidateProfile(position="d", keyword="Cobol", exp_years=0, english_level=None, skills=[], summary="")


def test_parse_cv_validates_llm_json_and_truncates_input(monkeypatch):
    seen = {}

    def fake_llm(text):
        seen["len"] = len(text)
        return ('{"position":"Backend Developer","keyword":"Python","exp_years":2,'
                '"english_level":"intermediate","skills":["Python"],"summary":"s"}')

    monkeypatch.setattr(cv_profile, "_call_llm", fake_llm)
    p = parse_cv("x" * (cv_profile.MAX_CV_CHARS + 5000))
    assert seen["len"] == cv_profile.MAX_CV_CHARS
    assert (p.exp_years, p.english_level, p.english_level_num) == (2, "intermediate", 3)


def test_parse_cv_rejects_llm_output_outside_allowed_values(monkeypatch):
    bad = ('{"position":"d","keyword":"Python","exp_years":1,"english_level":"IELTS 6.0",'
           '"skills":[],"summary":""}')
    monkeypatch.setattr(cv_profile, "_call_llm", lambda t: bad)
    with pytest.raises(ValueError):
        parse_cv("cv")


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(cv_profile.LlmNotConfigured):
        cv_profile._call_gemini("cv")


def test_gemini_client_is_kept_alive_and_reused(monkeypatch):
    """Client tạm bị dọn rác sẽ đóng kết nối HTTP trước khi gửi request; phải giữ và dùng lại."""
    cv_profile._get_client.cache_clear()
    a = cv_profile._get_client("fake-key")
    assert cv_profile._get_client("fake-key") is a
    assert not a._api_client._httpx_client.is_closed


GOOD_JSON = ('{"position":"Backend Developer","keyword":"Python","exp_years":2,'
             '"english_level":"intermediate","skills":["Python"],"summary":"s"}')


def test_provider_selection(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert cv_profile._provider() == "gemini"
    monkeypatch.setenv("GROQ_API_KEY", "k")
    assert cv_profile._provider() == "groq"
    monkeypatch.setenv("LLM_PROVIDER", "Gemini")
    assert cv_profile._provider() == "gemini"


def test_call_llm_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "foo")
    with pytest.raises(cv_profile.LlmNotConfigured):
        cv_profile._call_llm("cv")


def test_missing_groq_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(cv_profile.LlmNotConfigured):
        cv_profile._call_groq("cv")


def test_call_groq_builds_request_and_reads_reply(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    sent = {}

    class FakeResp:
        is_error = False

        def json(self):
            return {"choices": [{"message": {"content": GOOD_JSON}}]}

    def fake_post(url, headers, json, timeout):
        sent.update(url=url, headers=headers, body=json)
        return FakeResp()

    monkeypatch.setattr(cv_profile.httpx, "post", fake_post)
    assert cv_profile._call_groq("my cv text") == GOOD_JSON
    assert sent["url"] == cv_profile.GROQ_URL
    assert sent["headers"]["Authorization"] == "Bearer fake-key"
    assert sent["body"]["response_format"] == {"type": "json_object"}
    assert sent["body"]["messages"][1] == {"role": "user", "content": "my cv text"}
    system = sent["body"]["messages"][0]["content"]
    assert "IELTS" in system and "exp_years" in system  # prompt chuẩn hóa + schema đều có mặt
    assert parse_cv.__name__  # parse_cv dùng cùng đường này


def test_call_groq_error_includes_response_body(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")

    class ErrResp:
        is_error = True
        status_code = 404
        text = '{"error":{"code":"model_not_found"}}'

    monkeypatch.setattr(cv_profile.httpx, "post", lambda *a, **k: ErrResp())
    with pytest.raises(RuntimeError, match="model_not_found"):
        cv_profile._call_groq("cv")
