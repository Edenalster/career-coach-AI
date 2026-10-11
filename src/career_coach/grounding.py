import re
import unicodedata

_DASHES = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"), "-")
_QUOTES = {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"'}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_DASHES).translate(_QUOTES)
    text = re.sub(r"^[\s\-•*]+", "", text)        # leading bullet marker
    return re.sub(r"\s+", " ", text).strip().lower()


def is_grounded(quote: str, source: str) -> bool:
    """True if the quote appears (ignoring whitespace/case) in the source."""
    return bool(quote.strip()) and normalize(quote) in normalize(source)


def unsupported_skills(text: str, skills: list[str], source: str) -> list[str]:
    """Skills mentioned in `text` that appear nowhere in `source`."""
    text_n, source_n = normalize(text), normalize(source)
    found = []
    for s in skills:
        pat = r"(?<!\w)" + re.escape(normalize(s)) + r"(?!\w)"
        if re.search(pat, text_n) and not re.search(pat, source_n):
            found.append(s)
    return found