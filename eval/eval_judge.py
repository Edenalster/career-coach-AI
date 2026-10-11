import json
import os
from pathlib import Path

os.environ["NO_CACHE"] = "1"   # measure real behavior, not cached answers

from src.career_coach.validator import judge_claims

RUNS = 3
CHUNK = 12
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "eval/judge_cases.json"
cases = json.loads(Path(path).read_text(encoding="utf-8"))


def run_once() -> list[bool]:
    verdicts: list[bool] = []
    for i in range(0, len(cases), CHUNK):
        chunk = cases[i:i + CHUNK]
        verdicts += judge_claims([(c["claim"], c["evidence"]) for c in chunk])
    return verdicts


all_runs = [run_once() for _ in range(RUNS)]

# Positive class = "unsupported" (what the judge is supposed to catch)
for n, verdicts in enumerate(all_runs, 1):
    tp = fp = fn = tn = 0
    for c, said_supported in zip(cases, verdicts):
        truly_unsupported = not c["supported"]
        flagged = not said_supported
        if truly_unsupported and flagged:
            tp += 1
        elif flagged:
            fp += 1
        elif truly_unsupported:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    print(f"Run {n}: precision={precision:.2f} recall={recall:.2f} | "
          f"caught {tp}/{tp + fn} unsupported, falsely rejected {fp}/{fp + tn} supported")

print("\nMistakes in run 1:")
for c, v in zip(cases, all_runs[0]):
    if v != c["supported"]:
        kind = "MISSED (approved an unsupported claim)" if v else "FALSE REJECT (rejected a supported claim)"
        print(f"- {kind}: {c['claim']}")

unstable = [c["claim"] for i, c in enumerate(cases) if len({run[i] for run in all_runs}) > 1]
print(f"\nVerdict changed between runs for {len(unstable)} of {len(cases)} cases")
for u in unstable:
    print("-", u)