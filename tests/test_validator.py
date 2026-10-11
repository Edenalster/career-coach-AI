from src.career_coach import validator
from src.career_coach.nodes import interview_coach
from src.career_coach.schemas import (AnswerPoint, ClaimVerdict, ClaimVerdicts,
                                      GapReport, InterviewPrep, InterviewQuestion,
                                      JobProfile)

CV = "Skills: Python, Chroma, LangChain"


def test_missing_verdict_counts_as_unsupported(monkeypatch):
    fake = ClaimVerdicts(verdicts=[ClaimVerdict(index=0, supported=True, reason="ok")])
    monkeypatch.setattr(validator, "generate_structured", lambda *a, **k: fake)
    assert validator.judge_claims([("a", "x"), ("b", "y")]) == [True, False]


def test_judge_rejection_removes_point(monkeypatch):
    fake = InterviewPrep(questions=[InterviewQuestion(
        question="Why Chroma?", kind="technical", answer_points=[
            AnswerPoint(point="Chose Chroma for its Python API", cv_evidence="Skills: Python, Chroma, LangChain"),
        ])])
    monkeypatch.setattr(interview_coach, "generate_structured", lambda *a, **k: fake)
    monkeypatch.setattr(interview_coach, "judge_claims", lambda pairs: [False] * len(pairs))

    job = JobProfile(title="x", seniority="junior", must_have_skills=[],
                     nice_to_have_skills=[], responsibilities=[])
    result = interview_coach.prepare_interview(job, GapReport(matches=[], summary=""), CV)
    assert result.questions[0].answer_points == []