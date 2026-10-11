from ..llm import generate_structured
from ..schemas import JobProfile

SYSTEM = (
    "You extract structured information from job descriptions. Use only what is written. "
    "must_have_skills and nice_to_have_skills may contain ONLY concrete, verifiable items: technologies, tools, "
    "programming languages, qualifications (degree, years of experience) and spoken languages. "
    "Put personality traits and generic abilities (attention to detail, teamwork, communication, learning quickly, "
    "problem solving, interest in a domain) in soft_skills instead. "
    "Keep each skill short (at most 6 words)."
)

def analyze_job(job_text: str) -> JobProfile:
    return generate_structured(
        prompt=f"Extract the job profile from this job description:\n\n{job_text}",
        schema=JobProfile,
        system=SYSTEM,
    )