from src.career_coach.grounding import is_grounded, unsupported_skills

CV = "Built a RAG system with Chroma.\nSkills: Python"


def test_quote_found():
    assert is_grounded("rag system  with chroma", CV)


def test_quote_not_found():
    assert not is_grounded("Deployed with Docker", CV)


def test_unsupported_skill_detected():
    assert unsupported_skills("Deployed with Docker", ["Docker", "Python"], CV) == ["Docker"]


def test_word_boundary():
    assert unsupported_skills("cloud storage", ["RAG"], "nothing") == []

def test_unicode_dashes_and_bullets_are_normalized():
    cv = "- Led educational activities in an English-speaking summer camp."
    assert is_grounded("- Led educational activities in an English\u2011speaking summer camp.", cv)