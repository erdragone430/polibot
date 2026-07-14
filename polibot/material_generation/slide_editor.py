import json
import ollama
from pydantic import ValidationError

from polibot.config import get_settings
from polibot.material_generation.lessons import Slide
from polibot.material_generation.exercises import _extract_json_object, _fix_stray_backslashes
from polibot.retrieval.retriever import retrieve

MUTATE_PROMPT = (
    "You are an assistant slide editor. Below is a JSON description of a lesson slide, "
    "an editing instruction from the user, and some relevant context retrieved from the "
    "course database.\n\n"
    "Slide JSON:\n{slide_json}\n\n"
    "User editing instruction:\n{instruction}\n\n"
    "Retrieved Course Context:\n{context}\n\n"
    "Update the slide JSON according to the instruction. You can modify the title, content, "
    "latex_equation, html_widget, or accessibility_notes. "
    "Always write math using LaTeX macros (escape backslashes like \\\\frac, \\\\omega).\n"
    "Ensure you return ONLY valid JSON matching the Slide schema."
)


def mutate_slide(slide: Slide, instruction: str, course_id: str | None = None) -> Slide:
    settings = get_settings()

    # Retrieve relevant context from Qdrant using the instruction + slide content
    query_text = f"{instruction} {slide.title} {slide.content}"
    nodes = retrieve(query_text, top_k=2, course_id=course_id)
    context = "\n\n".join(f"- {n.node.get_content()}" for n in nodes)

    client = ollama.Client(host=settings.ollama_base_url)
    response = client.generate(
        model=settings.ollama_lesson_model,
        prompt=MUTATE_PROMPT.format(
            slide_json=slide.model_dump_json(),
            instruction=instruction,
            context=context or "(none found)",
        ),
        format=Slide.model_json_schema(),
    )

    raw = response["response"]
    try:
        return Slide.model_validate_json(_fix_stray_backslashes(raw))
    except ValidationError:
        pass
    return Slide.model_validate_json(_fix_stray_backslashes(_extract_json_object(raw)))
