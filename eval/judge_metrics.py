import json
import os
import time
from pathlib import Path

os.environ["NO_CACHE"] = "1"   # measure real behavior, not cached answers

from src.career_coach.llm import MODEL
from src.career_coach.validator import judge_claims

FILES = ["eval/judge_cases.json", "eval/judge_cases_hard.json"]
RUNS = 3
CHUNK = 12

cases = []
for f in FILES:
    cases += json.loads(Path(f).read_text(encoding="utf-8"))


def run_once() -> list[bool]:
    verdicts: list[bool] = []
    for i in range(0, len(cases), CHUNK):
        chunk = cases[i:i + CHUNK]
        verdicts += judge_claims([(c["claim"], c["evidence"]) for c in chunk])
    return verdicts


runs, seconds, errors = [], [], 0
for _ in range(RUNS):
    start = time.time()
    try:
        runs.append(run_once())
        seconds.append(time.time() - start)
    except Exception as e:
        errors += 1
        print(f"  run failed: {type(e).__name__}: {str(e)[:120]}")

precisions, recalls = [], []
for verdicts in runs:
    tp = fp = fn = 0
    for c, said_supported in zip(cases, verdicts):
        unsupported = not c["supported"]
        flagged = not said_supported
        tp += unsupported and flagged
        fp += (not unsupported) and flagged
        fn += unsupported and (not flagged)
    precisions.append(tp / (tp + fp) if tp + fp else 0.0)
    recalls.append(tp / (tp + fn) if tp + fn else 0.0)

unstable = sum(1 for i in range(len(cases)) if len({r[i] for r in runs}) > 1) if runs else None

result = {
    "model": MODEL,
    "cases": len(cases),
    "runs_ok": len(runs),
    "runs_failed": errors,
    "precision": round(sum(precisions) / len(precisions), 2) if precisions else None,
    "recall": round(sum(recalls) / len(recalls), 2) if recalls else None,
    "unstable_cases": unstable,
    "sec_per_run": round(sum(seconds) / len(seconds), 1) if seconds else None,
}
print("RESULT " + json.dumps(result))