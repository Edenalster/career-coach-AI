from pathlib import Path

from src.career_coach.graph import build_graph

job_text = Path("data/sample_job.txt").read_text(encoding="utf-8")
cv_text = Path("data/sample_cv.txt").read_text(encoding="utf-8")

state = build_graph().invoke({"job_text": job_text, "cv_text": cv_text})

print("\n=== GAPS ===")
for m in state["gaps"].matches:
    print(f"{m.status.upper():8} {m.skill} | {m.evidence}")

print(f"\n=== TAILORED BULLETS (attempts: {state['tailor_attempts']}) ===")
for b in state["tailored_bullets"]:
    original = " ".join(b.original.split()).lstrip("-• ")
    print(f"- [{b.targets_skill}] {b.rewritten}\n    (original: {original})")

print("\n=== INTERVIEW PREP ===")
for q in state["interview_prep"].questions:
    print(f"\n[{q.kind}] {q.question}")
    for p in q.answer_points:
        print(f"   • {p.point}\n       ↳ {p.cv_evidence or '(learning plan)'}")
        if not q.answer_points and q.kind != "gap":
            print("   (nothing in the CV supports an answer yet - prepare your own example)")
    for d in q.prepare_details:
        print(f"   ? {d}")