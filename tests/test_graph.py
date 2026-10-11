from src.career_coach import graph
from src.career_coach.graph import MAX_TAILOR_ATTEMPTS, route_after_tailor
from src.career_coach.schemas import TailoredBullet


def test_retry_when_rejections_and_attempts_left():
    assert route_after_tailor({"feedback": ["x"], "tailor_attempts": 1}) == "retry"


def test_stop_when_attempts_exhausted():
    assert route_after_tailor({"feedback": ["x"], "tailor_attempts": MAX_TAILOR_ATTEMPTS}) == "interview"


def test_continue_when_nothing_rejected():
    assert route_after_tailor({"feedback": [], "tailor_attempts": 1}) == "interview"


def test_graph_retries_rejected_rewrites_then_finishes(monkeypatch):
    calls = []

    def fake_round(job, gaps, cv_text, feedback=None):
        calls.append(feedback)
        if len(calls) == 1:
            return [], ["bad rewrite"]
        return [TailoredBullet(original="o", rewritten="r", targets_skill="s")], []

    monkeypatch.setattr(graph, "analyze_job", lambda text: "JOB")
    monkeypatch.setattr(graph, "parse_cv", lambda text: "CV")
    monkeypatch.setattr(graph, "analyze_gaps", lambda job, cv, text: "GAPS")
    monkeypatch.setattr(graph, "tailor_round", fake_round)
    monkeypatch.setattr(graph, "prepare_interview", lambda job, gaps, text: "PREP")

    state = graph.build_graph().invoke({"job_text": "j", "cv_text": "c"})

    assert calls == [None, ["bad rewrite"]]
    assert len(state["tailored_bullets"]) == 1
    assert state["tailor_attempts"] == 2
    assert state["interview_prep"] == "PREP"