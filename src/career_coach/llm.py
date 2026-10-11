import hashlib
import json
import os
import time
from pathlib import Path
from typing import Type, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "gemini")   # "gemini" | "openai_compat" | "ollama"

if PROVIDER == "gemini":
    from google import genai
    from google.genai import errors
    MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
elif PROVIDER == "openai_compat":
    import openai
    MODEL = os.environ["LLM_MODEL"]
    _oa = openai.OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )
elif PROVIDER == "ollama":
    import ollama
    MODEL = os.environ["OLLAMA_MODEL"]
else:
    raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}")

print(f"[llm] provider={PROVIDER} model={MODEL}")

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

T = TypeVar("T", bound=BaseModel)


def _generate_gemini(contents, system, schema) -> str:
    config = {}
    if system:
        config["system_instruction"] = system
    if schema:
        config["response_mime_type"] = "application/json"
        config["response_schema"] = schema

    for attempt in range(1, 6):
        try:
            response = _client.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
            return response.text
        except errors.APIError as e:
            if e.code == 429 and "PerDay" in str(e):
                raise RuntimeError(
                    "Daily free-tier quota exhausted. Switch model/provider or wait."
                ) from e
            if e.code in (429, 500, 503) and attempt < 5:
                print(f"  Retry {attempt} after error {e.code}...")
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("Model unavailable after several attempts")


def _generate_openai_compat(contents, system, schema) -> str:
    sys_msg = system or ""
    kwargs = {}
    if schema:
        sys_msg += (
            "\n\nReturn ONLY a JSON object that matches this JSON schema:\n"
            + json.dumps(schema.model_json_schema())
        )
        kwargs["response_format"] = {"type": "json_object"}

    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": contents},
    ]
    for attempt in range(1, 6):
        try:
            r = _oa.chat.completions.create(
                model=MODEL, messages=messages, temperature=0,
                max_completion_tokens=8192, **kwargs
            )
            choice = r.choices[0]
            if choice.finish_reason == "length":
                print("⚠️  Output was cut off (finish_reason=length) - raise max_completion_tokens")
            return choice.message.content
        except openai.APIStatusError as e:
            if e.status_code in (429, 500, 502, 503) and attempt < 5:
                print(f"  Retry {attempt} after error {e.status_code}...")
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("Model unavailable after several attempts")


def _generate_ollama(contents, system, schema) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": contents})
    response = ollama.chat(
        model=MODEL,
        messages=messages,
        format=schema.model_json_schema() if schema else None,
        options={"temperature": 0},
    )
    return response["message"]["content"]


def _generate(contents: str, system: str | None = None, schema: Type[BaseModel] | None = None) -> str:
    """One model call with a disk cache (key includes provider + model)."""
    key_src = json.dumps(
        {"provider": PROVIDER, "model": MODEL, "system": system,
         "contents": contents, "schema": json.dumps(schema.model_json_schema(), sort_keys=True) if schema else None,},
        sort_keys=True,
    )
    cache_file = CACHE_DIR / (hashlib.sha256(key_src.encode()).hexdigest() + ".txt")
    if not os.getenv("NO_CACHE") and cache_file.exists():
        return cache_file.read_text(encoding="utf-8")

    fn = {
        "gemini": _generate_gemini,
        "openai_compat": _generate_openai_compat,
        "ollama": _generate_ollama,
    }[PROVIDER]
    text = fn(contents, system, schema)
    if not os.getenv("NO_CACHE"):
        cache_file.write_text(text, encoding="utf-8")
    return text


def generate_structured(prompt: str, schema: Type[T], system: str | None = None, max_repairs: int = 2) -> T:
    """Get output validated against a Pydantic schema, with LLM auto-repair if invalid."""
    raw = _generate(prompt, system=system, schema=schema)
    for _ in range(max_repairs + 1):
        try:
            return schema.model_validate_json(raw)
        except ValidationError as e:
            repair_prompt = (
                f"The following JSON is invalid:\n{raw}\n\n"
                f"Validation error:\n{e}\n\n"
                "Return only the corrected JSON. Do not add or invent information."
            )
            raw = _generate(repair_prompt, schema=schema)
    raise ValueError("Could not produce valid structured output")