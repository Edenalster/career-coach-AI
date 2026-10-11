import json
import os
import re
from pathlib import Path

os.environ["NO_CACHE"] = "1"

from src.career_coach.llm import MODEL
from src.career_coach.nodes.job_analyzer import analyze_job


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9+#. ]+", " ", s.lower()).strip()


def matches(skill: str, group: list[str]) -> bool:
    s = norm(skill)
    return any(a and (norm(a) in s or (len(s) > 2 and s in norm(a))) for a in group)


import sys

path = sys.argv[1] if len(sys.argv) > 1 else "eval/job_cases.json"
cases = json.loads(Path(path).read_text(encoding="utf-8"))

gold_total = gold_found = pred_total = pred_correct = misplaced = 0
for c in cases:
    job = analyze_job(Path(c["file"]).read_text(encoding="utf-8"))
    gold_must, gold_nice = c["must_have"], c["nice_to_have"]

    for g in gold_must:
        gold_total += 1
        if any(matches(p, g) for p in job.must_have_skills):
            gold_found += 1
        else:
            print(f"[{c['id']}] MISSED must-have: {g[0]}")

    for p in job.must_have_skills:
        pred_total += 1
        if any(matches(p, g) for g in gold_must):
            pred_correct += 1
        elif any(matches(p, g) for g in gold_nice):
            misplaced += 1
            print(f"[{c['id']}] MISPLACED (nice-to-have listed as must): {p}")
        else:
            print(f"[{c['id']}] EXTRA (not in your labels): {p}")

recall = gold_found / gold_total if gold_total else 0.0
precision = pred_correct / pred_total if pred_total else 0.0
print(f"\nModel: {MODEL} | jobs: {len(cases)}")
print(f"Must-have recall={recall:.2f} precision={precision:.2f} | misplaced nice-to-have: {misplaced}")