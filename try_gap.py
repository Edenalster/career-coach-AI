from pathlib import Path

from src.career_coach.nodes.cv_parser import parse_cv
from src.career_coach.nodes.gap_analyzer import analyze_gaps
from src.career_coach.nodes.job_analyzer import analyze_job

job_text = Path("data/sample_job.txt").read_text(encoding="utf-8")
cv_text = Path("data/sample_cv.txt").read_text(encoding="utf-8")

job = analyze_job(job_text)
cv = parse_cv(cv_text)
report = analyze_gaps(job, cv, cv_text)
print("1/3 Analyzing job...")
job = analyze_job(job_text)
print("2/3 Parsing CV...")
cv = parse_cv(cv_text)
print("3/3 Analyzing gaps...")
report = analyze_gaps(job, cv, cv_text)

for m in report.matches:
    print(f"{m.status.upper():8} {m.skill}  |  {m.evidence}")
print("\nSummary:", report.summary)