import os

os.environ["NO_CACHE"] = "1"   # never store users' CVs on disk (must be set before importing llm)

import html
import inspect
from pathlib import Path

import gradio as gr

from src.career_coach.graph import build_graph
from src.career_coach.pdf_utils import extract_pdf_text, redact

MAX_CHARS = 15000
MAX_PDF_MB = 5
graph = build_graph()

STEP_LABELS = {
    "analyze_job": "Reading the job description",
    "parse_cv": "Parsing your CV",
    "analyze_gaps": "Comparing your CV with the requirements",
    "tailor": "Rewriting bullets and fact-checking them",
    "interview": "Preparing and verifying interview answers",
}
STATUS_STYLE = {
    "missing": ("Missing", "#ef4444"),
    "partial": ("Partial", "#f59e0b"),
    "match": ("Match", "#22c55e"),
}
KIND_STYLE = {"technical": "#6366f1", "behavioral": "#14b8a6", "gap": "#f59e0b"}


def esc(text) -> str:
    return html.escape(str(text or ""))


def pill(label: str, color: str) -> str:
    return (
        f'<span style="background:{color}22;color:{color};border:1px solid {color}66;'
        f'padding:2px 10px;border-radius:999px;font-size:0.78rem;font-weight:600;'
        f'white-space:nowrap">{esc(label)}</span>'
    )


def render_gaps(report, job) -> str:
    order = ["missing", "partial", "match"]
    matches = sorted(report.matches, key=lambda m: order.index(m.status))

    # Coverage is computed on must-have skills only
    must = {s.strip().lower() for s in job.must_have_skills}
    core = [m for m in matches if m.skill.strip().lower() in must] or matches
    n = {s: sum(1 for m in core if m.status == s) for s in STATUS_STYLE}
    total = len(core) or 1
    coverage = round(100 * (n["match"] + 0.5 * n["partial"]) / total)

    soft = ", ".join(esc(s) for s in job.soft_skills)
    soft_html = (
        f'<div style="opacity:.7;margin:8px 0;font-size:.85rem">Soft requirements (not scored): {soft}</div>'
        if soft else ""
    )

    rows = "".join(
        "<tr>"
        f'<td style="padding:8px 10px;vertical-align:top">{pill(*STATUS_STYLE[m.status])}</td>'
        f'<td style="padding:8px 10px;vertical-align:top;font-weight:600">{esc(m.skill)}</td>'
        f'<td style="padding:8px 10px;vertical-align:top;opacity:.8"><i>{esc(m.evidence) or "—"}</i></td>'
        "</tr>"
        for m in matches
    )
    return f"""
    <div style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;font-weight:600;margin-bottom:6px">
        <span>Must-have coverage <small style="opacity:.6">(partial counts as half)</small></span>
        <span>{coverage}%</span>
      </div>
      <div style="height:10px;border-radius:999px;background:rgba(128,128,128,.25);overflow:hidden">
        <div style="width:{coverage}%;height:100%;background:linear-gradient(90deg,#6366f1,#22c55e)"></div>
      </div>
      <div style="opacity:.75;margin-top:6px;font-size:.9rem">
        {n['match']} matched · {n['partial']} partial · {n['missing']} missing (of {len(core)} must-have requirements)
      </div>
    </div>
    {soft_html}
    <div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse">
      <thead><tr style="text-align:left;opacity:.7;font-size:.85rem">
        <th style="padding:6px 10px">Status</th><th style="padding:6px 10px">Skill</th>
        <th style="padding:6px 10px">Evidence from your CV</th>
      </tr></thead><tbody>{rows}</tbody></table></div>
    """

def render_bullets(bullets) -> str:
    if not bullets:
        return "Your existing bullets already match this job well, so no safe rewrite improved them."
    return "\n\n".join(
        f"**{b.targets_skill}**\n\n{b.rewritten}\n\n*Original: {' '.join(b.original.split()).lstrip('-• ')}*"
        for b in bullets
    )


def render_interview(prep) -> str:
    cards = []
    for q in prep.questions:
        points = "".join(
            f"<li>{esc(p.point)}<br><small style='opacity:.65'><i>↳ {esc(p.cv_evidence) or 'learning plan'}</i></small></li>"
            for p in q.answer_points
        )
        if not q.answer_points and q.kind != "gap":
            points = "<li style='opacity:.65'><i>Nothing in your CV supports an answer yet. Prepare your own example.</i></li>"
        prepare = "".join(f"<li>{esc(d)}</li>" for d in q.prepare_details)
        prepare_html = (
            "<div style='margin-top:8px;font-weight:600;font-size:.85rem'>Think about before the interview</div>"
            f"<ul>{prepare}</ul>"
            if prepare else ""
        )
        cards.append(
            "<details style='border:1px solid rgba(128,128,128,.35);border-radius:12px;padding:10px 14px;margin-bottom:10px'>"
            f"<summary style='cursor:pointer;font-weight:600'>{pill(q.kind, KIND_STYLE.get(q.kind, '#6366f1'))} &nbsp;{esc(q.question)}</summary>"
            f"<ul style='margin-top:8px'>{points}</ul>{prepare_html}</details>"
        )
    return "".join(cards) or "<i>No interview questions were generated.</i>"


def run(cv_text, job_text, progress=gr.Progress()):
    cv_text, job_text = (cv_text or "").strip(), (job_text or "").strip()
    if not cv_text or not job_text:
        raise gr.Error("Please provide both a CV (upload a PDF or paste text) and a job description.")
    if len(cv_text) > MAX_CHARS or len(job_text) > MAX_CHARS:
        raise gr.Error(f"Input too long (max {MAX_CHARS} characters each).")

    inputs = {"job_text": job_text, "cv_text": cv_text}
    state, done = dict(inputs), set()
    progress(0, desc="Starting")
    try:
        for update in graph.stream(inputs, stream_mode="updates"):
            for node, delta in update.items():
                state.update(delta)
                done.add(node)
                progress(len(done) / len(STEP_LABELS), desc=STEP_LABELS.get(node, node))
    except Exception as e:
        raise gr.Error(f"The model call failed ({type(e).__name__}). Try again in a minute.")

    return (
        render_gaps(state["gaps"], state["job"]),
        render_bullets(state["tailored_bullets"]),
        render_interview(state["interview_prep"]),
    )


def load_pdf(file):
    if not file:
        return gr.update()
    path = getattr(file, "name", file)
    if os.path.getsize(path) > MAX_PDF_MB * 1024 * 1024:
        raise gr.Error(f"PDF too large (max {MAX_PDF_MB} MB).")
    try:
        return redact(extract_pdf_text(path))
    except ValueError as e:
        raise gr.Error(str(e))
    except Exception:
        raise gr.Error("Could not read this PDF. Try another file, or paste the text instead.")


def load_sample():
    return (
        Path("data/sample_cv.txt").read_text(encoding="utf-8"),
        Path("data/sample_job.txt").read_text(encoding="utf-8"),
    )


THEME = gr.themes.Soft(primary_hue="indigo", secondary_hue="violet", neutral_hue="slate", radius_size="lg")
CSS = """
.hero {text-align:center; padding:8px 0 0}
.hero h1 {font-size:2.3rem; margin:0}
.hero p {opacity:.75; margin:.3rem 0 0}
"""

# Gradio 5 takes theme/css in Blocks(); Gradio 6 moved them to launch(). Support both.
_blocks_params = inspect.signature(gr.Blocks.__init__).parameters
_launch_params = inspect.signature(gr.Blocks.launch).parameters
_look = {"theme": THEME, "css": CSS}
blocks_kwargs = {k: v for k, v in _look.items() if k in _blocks_params}
launch_kwargs = {k: v for k, v in _look.items() if k in _launch_params and k not in _blocks_params}
if "delete_cache" in _blocks_params:
    blocks_kwargs["delete_cache"] = (60, 60)   # delete uploaded files (CVs) after about a minute

with gr.Blocks(title="Career Coach", **blocks_kwargs) as demo:
    gr.HTML(
        '<div class="hero"><h1>🧭 Career Coach</h1>'
        "<p>Upload your CV and a job description. Every claim is checked against your CV, so nothing is invented.</p></div>"
    )
    gr.Markdown(
        "🔒 **Privacy:** text is sent to a third-party LLM provider. Emails, phone numbers and links are removed "
        "from uploaded PDFs automatically, but please check the extracted text. The app stores nothing, and "
        "uploaded files are deleted within about a minute."
    )
    with gr.Row(equal_height=False):
        with gr.Column(scale=1):
            file_in = gr.File(label="Upload your CV (PDF)", file_types=[".pdf"])
            cv_in = gr.Textbox(
                label="CV text (review and edit if needed)", lines=12,
                placeholder="…or paste your CV here",
            )
            job_in = gr.Textbox(label="Job description", lines=10, placeholder="Paste the job posting here")
            with gr.Row():
                analyze_btn = gr.Button("Analyze", variant="primary", scale=3)
                sample_btn = gr.Button("Try a sample", scale=1)
        with gr.Column(scale=1):
            with gr.Tabs():
                with gr.Tab("Gap analysis"):
                    gaps_out = gr.HTML()
                with gr.Tab("Tailored bullets"):
                    bullets_out = gr.Markdown()
                with gr.Tab("Interview prep"):
                    interview_out = gr.HTML()

    file_in.upload(load_pdf, file_in, cv_in)
    sample_btn.click(load_sample, None, [cv_in, job_in])
    analyze_btn.click(run, [cv_in, job_in], [gaps_out, bullets_out, interview_out])

if __name__ == "__main__":
    demo.launch(**launch_kwargs)
    