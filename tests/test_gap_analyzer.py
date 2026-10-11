from src.career_coach.nodes import gap_analyzer
from src.career_coach.schemas import CVProfile, GapReport, JobProfile, SkillMatch

CV_TEXT = "- Led educational activities in an English-speaking summer camp."


def _run(monkeypatch, evidence):
    fake = GapReport(
        matches=[SkillMatch(skill="English", status="match", evidence=evidence)],
        summary="",
    )
    monkeypatch.setattr(gap_analyzer, "generate_structured", lambda *a, **k: fake)
    job = JobProfile(title="x", seniority="junior", must_have_skills=["English"],
                     nice_to_have_skills=[], responsibilities=[])
    cv = CVProfile(skills=[], experience=[], projects=[], education=[])
    return gap_analyzer.analyze_gaps(job, cv, CV_TEXT).matches[0]


def test_unicode_hyphen_in_evidence_still_counts_as_grounded(monkeypatch):
    m = _run(monkeypatch, "Led educational activities in an English\u2011speaking summer camp.")
    assert m.status == "match"


def test_invented_evidence_becomes_missing(monkeypatch):
    m = _run(monkeypatch, "Taught English at a university for five years")
    assert m.status == "missing"
    assert m.evidence == ""