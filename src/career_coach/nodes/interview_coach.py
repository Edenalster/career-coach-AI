from ..grounding import is_grounded
from ..llm import generate_structured
from ..schemas import GapReport, InterviewPrep, JobProfile
from ..validator import judge_claims

SYSTEM = (
    "You are an interview coach. Write 6-8 likely interview questions for the job: "
    "technical, behavioral, and 'gap' questions about skills the candidate lacks. "
    "For technical and behavioral questions, each answer point must be a plain first-person restatement "
    "of ONE specific CV bullet (project or experience), and cv_evidence must be that exact bullet or phrase. "
    "Do not add purposes, techniques, results, reasons or levels of expertise that the bullet does not state. "
    "Do not use the 'Skills:' line as evidence for how a tool was used. "
    "Short and simple points are better than impressive but unsupported ones. "
    "For 'gap' questions, points are honest learning plans and cv_evidence may be empty."
    "Also fill prepare_details with 2-3 short questions the candidate should think about to add "
    "real specifics (what was their own role, what metrics or results, what was hard and how they solved it). "
    "These are prompts for the candidate, never claims about her experience. "
    "cv_evidence must be a SHORT phrase (at most 15 words) copied character-for-character from the CV. "
    "A short exact quote is better than a long one that you slightly change. "
    "Include one 'gap' question for each of the 2-3 most important MISSING skills in the gap report. "
)


def prepare_interview(job: JobProfile, gaps: GapReport, cv_text: str) -> InterviewPrep:
    prompt = (
        f"Job profile:\n{job.model_dump_json(indent=2)}\n\n"
        f"Gap report:\n{gaps.model_dump_json(indent=2)}\n\n"
        f"CV text:\n{cv_text}"
    )
    result = generate_structured(prompt, InterviewPrep, system=SYSTEM)

    for q in result.questions:
        kept = []
        for p in q.answer_points:
            if q.kind == "gap" and not p.cv_evidence:
                kept.append(p)                      # learning plan, not a claim about the past
            elif is_grounded(p.cv_evidence, cv_text):
                kept.append(p)
            else:
                print(f"⚠️  Dropped unsupported point: {p.point[:60]}")
        q.answer_points = kept

        # LLM judge: does each quote really support its point?
    refs = [
        p for q in result.questions for p in q.answer_points if p.cv_evidence
    ]
    verdicts = judge_claims([(p.point, p.cv_evidence) for p in refs])
    rejected = {id(p) for p, ok in zip(refs, verdicts) if not ok}
    for q in result.questions:
        for p in q.answer_points:
            if id(p) in rejected:
                print(f"⚠️  Judge rejected: {p.point[:70]}")
        q.answer_points = [p for p in q.answer_points if id(p) not in rejected]
    return result