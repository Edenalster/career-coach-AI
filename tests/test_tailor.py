from src.career_coach.nodes import cv_tailor
from src.career_coach.schemas import (GapReport, JobProfile, SkillMatch,
                                      TailoredBullet, TailoredCV)

CV = "Built a RAG system with Chroma.\nSkills: Python"


def test_hallucinated_rewrite_is_dropped(monkeypatch):
    fake = TailoredCV(bullets=[
        TailoredBullet(original="Built a RAG system with Chroma",
                       rewritten="Built a RAG system using Chroma vector search",
                       targets_skill="RAG"),
        TailoredBullet(original="Built a RAG system with Chroma",
                       rewritten="Deployed a RAG system with Docker",
                       targets_skill="Docker"),
    ])
    monkeypatch.setattr(cv_tailor, "generate_structured", lambda *a, **k: fake)
    monkeypatch.setattr(cv_tailor, "judge_claims", lambda pairs: [True] * len(pairs))

    job = JobProfile(title="Junior AI Engineer", seniority="junior",
                     must_have_skills=["RAG"], nice_to_have_skills=["Docker"],
                     responsibilities=[])
    gaps = GapReport(matches=[SkillMatch(skill="RAG", status="match",
                                         evidence="Built a RAG system with Chroma")],
                     summary="")

    result = cv_tailor.tailor_cv(job, gaps, CV)
    assert len(result.bullets) == 1
    assert "Docker" not in result.bullets[0].rewritten

def test_bullet_with_wrong_label_is_rejected(monkeypatch):
    cv = "Implemented JWT authentication and Swagger docs"
    bullet = TailoredBullet(
        original=cv,
        rewritten="Implemented JWT authentication and Swagger documentation",
        targets_skill="SQL",
    )
    monkeypatch.setattr(cv_tailor, "generate_structured", lambda *a, **k: TailoredCV(bullets=[bullet]))
    answers = iter([[True], [False]])   # 1st judge call: rewrite is faithful. 2nd: the label is wrong
    monkeypatch.setattr(cv_tailor, "judge_claims", lambda pairs: next(answers))

    job = JobProfile(title="x", seniority="junior", must_have_skills=["SQL"],
                     nice_to_have_skills=[], responsibilities=[])
    accepted, rejected = cv_tailor.tailor_round(job, GapReport(matches=[], summary=""), cv)

    assert accepted == []
    assert len(rejected) == 1