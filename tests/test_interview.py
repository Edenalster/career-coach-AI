from src.career_coach.nodes import interview_coach
from src.career_coach.schemas import (AnswerPoint, GapReport, InterviewPrep,
                                      InterviewQuestion, JobProfile)

CV = "Built a RAG system with Chroma.\nSkills: Python"


def test_unsupported_points_are_dropped(monkeypatch):
    fake = InterviewPrep(questions=[
        InterviewQuestion(question="Tell me about RAG", kind="technical", answer_points=[
            AnswerPoint(point="Built a RAG system", cv_evidence="Built a RAG system with Chroma"),
            AnswerPoint(point="Deployed it to production", cv_evidence="Deployed to AWS"),
        ]),
        InterviewQuestion(question="No Docker?", kind="gap", answer_points=[
            AnswerPoint(point="Would take a Docker course", cv_evidence=""),
        ]),
    ])
    monkeypatch.setattr(interview_coach, "generate_structured", lambda *a, **k: fake)
    monkeypatch.setattr(interview_coach, "judge_claims", lambda pairs: [True] * len(pairs))

    job = JobProfile(title="x", seniority="junior", must_have_skills=[],
                     nice_to_have_skills=[], responsibilities=[])
    result = interview_coach.prepare_interview(job, GapReport(matches=[], summary=""), CV)

    assert [p.point for p in result.questions[0].answer_points] == ["Built a RAG system"]
    assert len(result.questions[1].answer_points) == 1   # learning plan is kept