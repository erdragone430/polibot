import ollama
from polibot.config import get_settings
from polibot.material_generation.lessons import Slide
from polibot.material_generation.slide_editor import mutate_slide


def test_slide_editing():
    print("--- Running Slide Mutation Test ---")
    settings = get_settings()

    client = ollama.Client(host=settings.ollama_base_url)
    client.list()
    print("Connected to active local Ollama/Qdrant servers.")

    original_slide = Slide(
        title="Derivative Maximization",
        content="To find the absolute maximum of a function on an interval, find the critical points by taking the derivative and setting it to zero.",
        latex_equation="f'(x) = 0",
        accessibility_notes="Standard paragraph explanation",
    )

    print("\n[Original Slide JSON]")
    print(original_slide.model_dump_json(indent=2))

    instruction = "shorten the explanation and add a critical warning about boundary condition traps in exam questions"
    print(f"\n[Applying Instruction: '{instruction}']")

    updated_slide = mutate_slide(
        slide=original_slide,
        instruction=instruction,
        course_id="tenant_test_course",
    )

    print("\n[Mutated Slide JSON]")
    print(updated_slide.model_dump_json(indent=2))

    assert (
        updated_slide.title != ""
    ), "Title should be present."
    assert (
        len(updated_slide.content) > 0
    ), "Content should be present."

    print("\n>>> SLIDE EDITING TEST PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    test_slide_editing()
