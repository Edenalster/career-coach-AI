from ..grounding import is_grounded, unsupported_skills
from ..llm import generate_structured
from ..schemas import GapReport, JobProfile, TailoredBullet, TailoredCV
from ..validator import judge_claims
from ..grounding import is_grounded, normalize, unsupported_skills

SYSTEM = (
    "You improve CV bullet points for a target job. "
    "Choose at most 6 bullets from the Projects and Professional Experience sections that best support the job's "
    "must-have skills. For each, set targets_skill to ONE requirement copied exactly from the allowed list, "
    "and only if the bullet genuinely supports it. Use each requirement at most twice. "
    "Rules: (1) 'original' must be copied EXACTLY from the CV. "
    "(2) Reword only to make the relevance clearer (lead with the relevant tool or outcome, remove filler). "
    "Never add tools, skills, numbers, purposes or technical details that are not in the original bullet. "
    "(3) Never claim skills listed as missing. "
    "(4) If a bullet needs no change, skip it. "
    "(5) Do not use words of level or expertise ('proficient', 'skilled', 'experienced') unless the original does."
)


def tailor_round(job: JobProfile, gaps: GapReport, cv_text: str, feedback: list[str] | None = None):
    """One attempt. Returns (accepted_bullets, rejected_rewrites)."""
    supported = [m.skill for m in gaps.matches if m.status != "missing"]
    missing = [m.skill for m in gaps.matches if m.status == "missing"]
    prompt = (
        f"Target job: {job.title}\n"
        f"Allowed targets_skill values: {job.must_have_skills + job.nice_to_have_skills}\n"
        f"Must-have skills (prioritize): {job.must_have_skills}\n"
        f"Skills the candidate has (emphasize these): {supported}\n"
        f"Skills the candidate lacks (do NOT claim): {missing}\n\n"
        f"CV text:\n{cv_text}"
    )
    if feedback:
        prompt += (
            "\n\nThese earlier rewrites were REJECTED (the reason follows each one):\n" + "\n".join(f"- {f}" for f in feedback) +
            "\nRewrite those bullets again, staying much closer to the original wording. "
            "Do not add tools, purposes, techniques or technical roles that the original does not state."
        )
    result = generate_structured(prompt, TailoredCV, system=SYSTEM)

    job_skills = job.must_have_skills + job.nice_to_have_skills
    candidates: list[TailoredBullet] = []
    rejected: list[str] = []
    for b in result.bullets:
        b.rewritten = b.rewritten.lstrip("-• ").strip()
        if b.targets_skill not in set(job.must_have_skills + job.nice_to_have_skills):
            print(f"⚠️  Skipped: targets_skill not in the job's requirements -> {b.targets_skill[:50]}")
            continue
        if normalize(b.rewritten) == normalize(b.original):
            continue   # nothing to improve
        if not is_grounded(b.original, cv_text):
            print(f"⚠️  Dropped: original not found in CV -> {b.original[:50]}")
            continue
        bad = unsupported_skills(b.rewritten, job_skills, cv_text)
        if bad:
            print(f"⚠️  Rejected: rewrite introduces unsupported skills {bad}")
            rejected.append(f"{b.rewritten}  <-- original: {b.original}")
            continue
        candidates.append(b)

    verdicts = judge_claims([(b.rewritten, b.original) for b in candidates])
    accepted: list[TailoredBullet] = []
    for b, ok in zip(candidates, verdicts):
        if ok:
            accepted.append(b)
        else:
            print(f"⚠️  Judge rejected rewrite: {b.rewritten[:70]}")
            rejected.append(f"{b.rewritten}  <-- original: {b.original}")
        # Does each bullet really demonstrate the requirement it is labelled with?
    label_ok = judge_claims(
        [(f"This bullet demonstrates: {b.targets_skill}", b.original) for b in accepted]
    )
    final: list[TailoredBullet] = []
    for b, ok in zip(accepted, label_ok):
        if ok:
            final.append(b)
        else:
            print(f"⚠️  Wrong label: '{b.targets_skill}' is not shown by: {b.original[:60]}")
            rejected.append(
                f"{b.rewritten}  <-- labelled '{b.targets_skill}', but the original bullet does not show that skill. "
                "Pick a different requirement, or skip this bullet."
            )
    return final, rejected


def tailor_cv(job: JobProfile, gaps: GapReport, cv_text: str) -> TailoredCV:
    """Single attempt, no retry (the graph handles retries)."""
    accepted, _ = tailor_round(job, gaps, cv_text)
    return TailoredCV(bullets=accepted)