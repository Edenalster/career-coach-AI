import json
import os
import subprocess
import sys
from pathlib import Path

MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]   # add more model names from your provider's list

rows = []
for m in MODELS:
    print(f"Running {m} ...")
    # Environment variables set here take priority over .env (load_dotenv does not override)
    proc = subprocess.run(
        [sys.executable, "-m", "eval.judge_metrics"],
        env={**os.environ, "LLM_MODEL": m},
        capture_output=True, text=True,
    )
    line = [l for l in proc.stdout.splitlines() if l.startswith("RESULT ")]
    if not line:
        print(f"  {m} failed:\n{proc.stderr[-600:]}")
        continue
    rows.append(json.loads(line[-1][len("RESULT "):]))

header = "| Model | Cases | Precision | Recall | Unstable cases | Sec/run | Failed runs |\n|---|---|---|---|---|---|---|\n"
body = "".join(
    f"| {r['model']} | {r['cases']} | {r['precision']} | {r['recall']} | "
    f"{r['unstable_cases']} | {r['sec_per_run']} | {r['runs_failed']} |\n"
    for r in rows
)
table = header + body
print("\n" + table)
Path("eval/results.md").write_text(table, encoding="utf-8")
print("Saved to eval/results.md")