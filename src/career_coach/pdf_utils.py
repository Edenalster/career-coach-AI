import re
import unicodedata

from pypdf import PdfReader

MAX_PAGES = 5
MIN_CHARS = 200

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL = re.compile(r"(?:https?://|www\.)\S+|\b(?:linkedin\.com|github\.com)/\S+", re.I)
_PHONE = re.compile(r"(?<![\w])\+?\d[\d ().-]{7,}\d(?![\w])")


def _drop_phone(m: re.Match) -> str:
    # 9+ digits = phone number; shorter matches are usually date ranges like 2020-2022
    return "" if len(re.sub(r"\D", "", m.group())) >= 9 else m.group()


def redact(text: str) -> str:
    """Remove emails, links and phone numbers before the text goes to an LLM."""
    text = _EMAIL.sub("", text)
    text = _URL.sub("", text)
    return _PHONE.sub(_drop_phone, text)


def clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)   # also fixes ligatures such as "ﬁ"
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("This PDF is password-protected. Remove the password or paste the text.")
    if len(reader.pages) > MAX_PAGES:
        raise ValueError(f"The PDF has more than {MAX_PAGES} pages. A CV should be shorter.")
    text = clean("\n".join(page.extract_text() or "" for page in reader.pages))
    if len(text) < MIN_CHARS:
        raise ValueError("No readable text found. The PDF may be a scanned image. Paste the text instead.")
    return text