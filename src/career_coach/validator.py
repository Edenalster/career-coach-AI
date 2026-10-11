from .llm import generate_structured
from .schemas import ClaimVerdicts

SYSTEM = (
    "You are a fact-checker for CV claims. For each numbered item you get a CLAIM and the "
    "EVIDENCE quoted from the candidate's CV. "
    "Mark supported=true if the claim is a faithful restatement or summary of the evidence: "
    "same tools, same actions, same outcome. Paraphrasing, reordering and first-person phrasing are fine. "
    "Mark supported=false ONLY if the claim adds a NEW specific fact that is not in the evidence: "
    "a tool, a technique, a number or result, a purpose or reason, a level of expertise "
    "(such as 'solid' or 'expert'), or details of HOW a skill was used when the evidence only lists it.\n"
    "Examples:\n"
    "- Evidence: 'Built a recommendation system using LLMs and Chroma.' "
    "Claim: 'I built a recommendation system with LLMs and Chroma.' -> supported=true\n"
    "- Same evidence. Claim: 'I used Chroma for efficient similarity search.' -> supported=false (adds a purpose)\n"
    "- Evidence: 'Skills: Python, Chroma.' Claim: 'I used Chroma to build a search engine.' -> supported=false (skills list only)\n"
    "Return one verdict per item with a short reason."
    "- Evidence: 'Programming languages: Python, Java.' Claim: 'Proficient in Python and Java.' "
    "-> supported=false (adds a level of expertise)\n"
)


def judge_claims(pairs: list[tuple[str, str]]) -> list[bool]:
    """pairs = [(claim, evidence), ...] -> list of booleans (True = supported)."""
    if not pairs:
        return []
    listing = "\n\n".join(
        f"[{i}]\nCLAIM: {claim}\nEVIDENCE: {evidence}"
        for i, (claim, evidence) in enumerate(pairs)
    )
    result = generate_structured(
        prompt=f"Check each item:\n\n{listing}",
        schema=ClaimVerdicts,
        system=SYSTEM,
    )
    verdicts = {v.index: v.supported for v in result.verdicts}
    # A missing verdict counts as unsupported (fail closed)
    return [verdicts.get(i, False) for i in range(len(pairs))]