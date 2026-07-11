import ollama
from pydantic import BaseModel, ValidationError

from polibot.config import get_settings
from polibot.material_generation.exercises import _extract_json_object, _fix_stray_backslashes
from polibot.retrieval.retriever import retrieve

TEMPLATE_POOL_SIZE = 3

LESSON_PROMPT = (
    "You are a course lesson author. Below are reference excerpts from the course "
    "material on related topics. Write a personalized lesson about '{topic}' as a "
    "sequence of between {min_slides} and {max_slides} slides (inclusive), each with "
    "a short title and its content, following the same style and depth as the "
    "reference material.\n\n"
    "Always write math using LaTeX macros (e.g. \\omega, \\Delta, \\varphi, \\theta, "
    "\\alpha, \\beta) instead of literal Unicode symbols (ω, ∆, φ, θ, α, β, ...).\n\n"
    "Reference material:\n{examples}"
)


class Slide(BaseModel):
    title: str
    content: str


class Lesson(BaseModel):
    topic: str
    slides: list[Slide]


def generate_lesson(
    topic: str, min_slides: int, max_slides: int, template_count: int = TEMPLATE_POOL_SIZE, **extra_params
) -> Lesson:
    templates = retrieve(topic, top_k=template_count)
    examples = "\n\n".join(f"- {node.node.get_content()}" for node in templates)

    settings = get_settings()
    client = ollama.Client(host=settings.ollama_base_url)
    response = client.generate(
        model=settings.ollama_lesson_model,
        prompt=LESSON_PROMPT.format(
            topic=topic,
            min_slides=min_slides,
            max_slides=max_slides,
            examples=examples or "(none found)",
        ),
        format=Lesson.model_json_schema(),
        **extra_params,
    )
    raw = response["response"]
    try:
        return Lesson.model_validate_json(_fix_stray_backslashes(raw))
    except ValidationError:
        pass
    return Lesson.model_validate_json(_fix_stray_backslashes(_extract_json_object(raw)))
