from ..grounding import is_grounded
from ..llm import generate_structured
from ..schemas import CVProfile, GapReport, JobProfile

SYSTEM = (
    "You compare a job profile with a candidate's CV. For every skill in the job's "
    "must-have and nice-to-have lists, decide: match, partial or missing. "
    "For match and partial, 'evidence' MUST be a short quote copied EXACTLY from the CV text. "
    "If there is no support in the CV, status is 'missing' and evidence is an empty string. "
    "Never invent experience."
    "Evidence must show the skill was actually used (a project or experience bullet). "
    "A certificate or course title alone is only 'partial'. "
    "Prefer evidence from Projects or Professional Experience bullets over the Skills list. "
    "If the only evidence is a line from the Skills list, the status is 'partial'. "
)



def analyze_gaps(job: JobProfile, cv: CVProfile, cv_text: str) -> GapReport:
    prompt = (
        f"Job profile:\n{job.model_dump_json(indent=2)}\n\n"
        f"CV profile:\n{cv.model_dump_json(indent=2)}\n\n"
        f"Original CV text (quote evidence from here):\n{cv_text}"
    )
    report = generate_structured(prompt=prompt, schema=GapReport, system=SYSTEM)

    # Grounding check: evidence must really appear in the CV
    for m in report.matches:
        if m.status != "missing" and not is_grounded(m.evidence, cv_text):
            print(f"⚠️  Ungrounded evidence for '{m.skill}': {m.evidence[:60]!r} -> marked as missing")
            m.status = "missing"
            m.evidence = ""
    return report