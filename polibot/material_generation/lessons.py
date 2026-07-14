import ollama
from pydantic import BaseModel, ValidationError

from polibot.config import get_settings
from polibot.material_generation.exercises import _extract_json_object, _fix_stray_backslashes
from polibot.retrieval.retriever import retrieve

TEMPLATE_POOL_SIZE = 3

LESSON_PROMPT = (
    "You are a course lesson author acting as a multi-agent supervisor orchestrating three specialists:\n"
    "1. LaTeX Specialist: extracts/generates standard mathematical formulas as LaTeX equations.\n"
    "2. Interactive HTML Widget Specialist: generates raw self-contained HTML/CSS/JS (no external script tags, single block) for any interactive demo matching the slide (e.g. limit sliders, coordinate plots, dynamic vectors) if the profile is 'visual'.\n"
    "3. Accessibility Specialist: optimizes text structure (short, bulleted lists for 'adhd'; spaced text or high-contrast cues for 'dyslexia').\n\n"
    "Write a personalized lesson about '{topic}' as a sequence of between {min_slides} and {max_slides} slides (inclusive).\n"
    "Learner profile target: {style_profile}.\n\n"
    "For each slide, return:\n"
    "- title: slide title\n"
    "- content: slide body text (reformatted based on target profile)\n"
    "- latex_equation: a relevant LaTeX equation (mandatory if math is involved, escape backslashes)\n"
    "- html_widget: self-contained HTML widget block if style_profile is 'visual' (otherwise null)\n"
    "- accessibility_notes: brief guidance matching the profile (e.g. 'high-contrast listing style' or 'tactile slider visualizer')\n\n"
    "Always write math using LaTeX macros (e.g. \\omega, \\Delta, \\varphi, \\theta, "
    "\\alpha, \\beta) instead of literal Unicode symbols (ω, ∆, φ, θ, α, β, ...).\n\n"
    "Reference material:\n{examples}"
)


class Slide(BaseModel):
    title: str
    content: str
    latex_equation: str | None = None
    html_widget: str | None = None
    accessibility_notes: str | None = None


class Lesson(BaseModel):
    topic: str
    slides: list[Slide]


def generate_lesson(
    topic: str,
    min_slides: int,
    max_slides: int,
    style_profile: str = "standard",
    template_count: int = TEMPLATE_POOL_SIZE,
    **extra_params,
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
            style_profile=style_profile,
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
