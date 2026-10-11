from ..llm import generate_structured
from ..schemas import CVProfile

SYSTEM = (
    "You extract structured information from a CV. "
    "Copy experience and project bullet points as they appear in the CV. "
    "Do not add, improve or invent anything."
)

def parse_cv(cv_text: str) -> CVProfile:
    return generate_structured(
        prompt=f"Extract the profile from this CV:\n\n{cv_text}",
        schema=CVProfile,
        system=SYSTEM,
    )