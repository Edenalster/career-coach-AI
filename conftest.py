import os

os.environ.setdefault("LLM_PROVIDER", "openai_compat")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("LLM_BASE_URL", "http://localhost")
os.environ.setdefault("LLM_API_KEY", "test")