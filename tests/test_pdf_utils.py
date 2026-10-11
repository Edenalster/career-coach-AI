import pytest
from pypdf import PdfWriter

from src.career_coach.pdf_utils import clean, extract_pdf_text, redact


def test_redact_removes_contact_details_but_keeps_date_ranges():
    text = (
        "Phone 054-1234567\nMail jane.doe@example.com\n"
        "https://github.com/janedoe\nlinkedin.com/in/janedoe\n"
        "Administrative Manager (2020-2022)"
    )
    out = redact(text)
    assert "1234567" not in out
    assert "@" not in out
    assert "github" not in out
    assert "linkedin" not in out
    assert "2020-2022" in out


def test_clean_normalizes_ligatures():
    assert clean("e\ufb00ective o\ufb03ce") == "effective office"


def test_pdf_without_text_is_rejected(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    path = tmp_path / "blank.pdf"
    with open(path, "wb") as f:
        writer.write(f)
    with pytest.raises(ValueError):
        extract_pdf_text(str(path))