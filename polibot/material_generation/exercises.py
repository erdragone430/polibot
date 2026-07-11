import json
import re
from typing import Any

import ollama
from pydantic import BaseModel, ValidationError

from polibot.config import get_settings
from polibot.generation.llm import _cloud_client
from polibot.retrieval.retriever import retrieve

TEMPLATE_POOL_SIZE = 3

EXERCISE_PROMPT = (
    "You are a course exercise author. Below are example exercises from the course "
    "material on related topics. Write ONE new exercise about '{topic}' that follows "
    "the same structure and difficulty as the examples, but uses different data/numbers "
    "and phrasing so it isn't a duplicate.\n\n"
    "Always write math using LaTeX macros (e.g. \\omega, \\Delta, \\varphi, \\theta, "
    "\\alpha, \\beta) instead of literal Unicode symbols (ω, ∆, φ, θ, α, β, ...).\n\n"
    "Examples:\n{examples}"
)

REPAIR_PROMPT = (
    "Convert the following exercise into JSON matching the required schema, with a "
    "'statement' string, a 'data' object of the exercise's numeric/given values, and a "
    "'solution' string. Output only the JSON.\n\nExercise:\n{text}"
)


class Exercise(BaseModel):
    statement: str
    data: dict[str, Any]
    solution: str


_STRAY_BACKSLASH_RE = re.compile(r"(?<!\\)\\(?!u[0-9a-fA-F]{4})(?=[a-z]{2,})")


def _fix_stray_backslashes(text: str) -> str:
    """Double any backslash that precedes a lowercase multi-letter LaTeX command (e.g. \\frac, \\beta).

    LLMs often emit LaTeX inside JSON strings without escaping the backslash. Since
    \\b, \\f, \\n, \\r, \\t are all valid JSON string escapes, json.loads silently
    decodes them into control characters instead of raising an error, corrupting
    the LaTeX command (e.g. "\\frac" -> "\x0crac"). Standard LaTeX macro names are
    conventionally all-lowercase and 2+ letters (frac, beta, nu, tan...), so that's
    the trigger for "this needs escaping". A single stray letter, or a letter run
    that turns uppercase (e.g. "\\nThis", a paragraph break before a new sentence),
    is left untouched and decoded as a real JSON whitespace escape instead -
    otherwise legitimate newlines/tabs in prose get corrupted. A real \\uXXXX
    unicode escape is also left untouched, as are already-doubled backslashes.
    Uppercase-led commands (\\Gamma, \\LaTeX) aren't silently corrupted by json.loads
    in the first place -- their leading letter isn't a valid JSON escape, so they
    already hard-fail into the extract/repair fallback rather than needing this fix.
    """
    return _STRAY_BACKSLASH_RE.sub(r"\\\\", text)


def _extract_json_object(text: str) -> str:
    """Find the first balanced {...} JSON object in free-form text.

    Ollama Cloud models don't always honor the `format` schema constraint
    and may wrap the JSON in markdown commentary.
    """
    decoder = json.JSONDecoder()
    for i, char in enumerate(text):
        if char == "{":
            try:
                _, end = decoder.raw_decode(text, i)
                return text[i:end]
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON object found in response")


def generate_exercise(topic: str, template_count: int = TEMPLATE_POOL_SIZE) -> Exercise:
    templates = retrieve(topic, top_k=template_count)
    examples = "\n\n".join(f"- {node.node.get_content()}" for node in templates)

    settings = get_settings()
    client = _cloud_client()
    response = client.generate(
        model=settings.ollama_model,
        prompt=EXERCISE_PROMPT.format(topic=topic, examples=examples or "(none found)"),
        format=Exercise.model_json_schema(),
    )
    raw = response["response"]
    try:
        return Exercise.model_validate_json(_fix_stray_backslashes(raw))
    except ValidationError:
        pass

    try:
        return Exercise.model_validate_json(_fix_stray_backslashes(_extract_json_object(raw)))
    except (ValueError, ValidationError):
        pass

    # Ollama Cloud doesn't always honor the `format` schema constraint and may
    # return pure markdown with no JSON at all; repair it with a local model
    # that does honor structured output.
    local_client = ollama.Client(host=settings.ollama_base_url)
    repair_response = local_client.generate(
        model=settings.ollama_reformulation_model,
        prompt=REPAIR_PROMPT.format(text=raw),
        format=Exercise.model_json_schema(),
    )
    return Exercise.model_validate_json(_fix_stray_backslashes(repair_response["response"]))
