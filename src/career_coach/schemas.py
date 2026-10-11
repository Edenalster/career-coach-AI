from pydantic import BaseModel, Field
from typing import List, Literal


class JobProfile(BaseModel):
    title: str
    seniority: Literal["intern", "junior", "mid", "senior", "unknown"]
    must_have_skills: List[str]
    nice_to_have_skills: List[str]
    responsibilities: List[str]
    soft_skills: List[str] = Field(default_factory=list)


class CVProfile(BaseModel):
    skills: List[str]
    experience: List[str] = Field(description="Original bullet points from the CV, used as evidence")
    projects: List[str]
    education: List[str]


class SkillMatch(BaseModel):
    skill: str
    status: Literal["match", "partial", "missing"]
    evidence: str = Field(description="Quote from the CV supporting this, or empty if missing")


class GapReport(BaseModel):
    matches: List[SkillMatch]
    summary: str

class TailoredBullet(BaseModel):
    original: str = Field(description="Exact original bullet copied from the CV")
    rewritten: str = Field(description="Reworded for relevance to the job; no new facts")
    targets_skill: str


class TailoredCV(BaseModel):
    bullets: List[TailoredBullet]


class AnswerPoint(BaseModel):
    point: str
    cv_evidence: str = Field(
        description="Exact quote from the CV supporting this point. "
                    "Empty ONLY for learning plans in 'gap' questions."
    )


class InterviewQuestion(BaseModel):
    question: str
    kind: Literal["technical", "behavioral", "gap"]
    answer_points: List[AnswerPoint]
    prepare_details: List[str] = Field(
        default_factory=list,
        description="2-3 questions the candidate should answer for themselves to add specifics "
                    "the CV lacks (their role, metrics, challenges, decisions). Prompts, not claims.",
    )

class InterviewPrep(BaseModel):
    questions: List[InterviewQuestion]

class ClaimVerdict(BaseModel):
    index: int
    supported: bool
    reason: str


class ClaimVerdicts(BaseModel):
    verdicts: List[ClaimVerdict]