from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .nodes.cv_parser import parse_cv
from .nodes.cv_tailor import tailor_round
from .nodes.gap_analyzer import analyze_gaps
from .nodes.interview_coach import prepare_interview
from .nodes.job_analyzer import analyze_job

MAX_TAILOR_ATTEMPTS = 3


class State(TypedDict, total=False):
    job_text: str
    cv_text: str
    job: Any
    cv: Any
    gaps: Any
    tailored_bullets: list
    feedback: list
    tailor_attempts: int
    interview_prep: Any


def job_node(state: State):
    return {"job": analyze_job(state["job_text"])}


def cv_node(state: State):
    return {"cv": parse_cv(state["cv_text"])}


def gaps_node(state: State):
    return {"gaps": analyze_gaps(state["job"], state["cv"], state["cv_text"])}


def tailor_node(state: State):
    attempts = state.get("tailor_attempts", 0) + 1
    accepted, rejected = tailor_round(
        state["job"], state["gaps"], state["cv_text"], feedback=state.get("feedback")
    )
    kept = {b.original: b for b in state.get("tailored_bullets", [])}
    for b in accepted:
        kept[b.original] = b
    return {
        "tailored_bullets": list(kept.values()),
        "feedback": rejected,
        "tailor_attempts": attempts,
    }


def interview_node(state: State):
    return {"interview_prep": prepare_interview(state["job"], state["gaps"], state["cv_text"])}


def route_after_tailor(state: State) -> str:
    if state.get("feedback") and state.get("tailor_attempts", 0) < MAX_TAILOR_ATTEMPTS:
        return "retry"
    return "interview"


def build_graph():
    g = StateGraph(State)
    g.add_node("analyze_job", job_node)
    g.add_node("parse_cv", cv_node)
    g.add_node("analyze_gaps", gaps_node)
    g.add_node("tailor", tailor_node)
    g.add_node("interview", interview_node)

    g.add_edge(START, "analyze_job")
    g.add_edge("analyze_job", "parse_cv")
    g.add_edge("parse_cv", "analyze_gaps")
    g.add_edge("analyze_gaps", "tailor")
    g.add_conditional_edges("tailor", route_after_tailor, {"retry": "tailor", "interview": "interview"})
    g.add_edge("interview", END)
    return g.compile()