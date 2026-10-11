from src.career_coach.llm import generate_structured
from src.career_coach.schemas import JobProfile

job_description = """
Junior AI Engineer. We are looking for a developer with Python experience
and familiarity with RAG, vector databases and LLM APIs. Docker is a plus.
You will build and evaluate AI features with our product team.
"""

result = generate_structured(
    prompt=f"Extract the job profile from this job description:\n\n{job_description}",
    schema=JobProfile,
    system="You extract structured information from job descriptions. Use only what is written.",
)
print(result.model_dump_json(indent=2))