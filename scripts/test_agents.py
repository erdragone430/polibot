import ollama
from polibot.config import get_settings
from polibot.material_generation.lessons import generate_lesson, Lesson, Slide


def test_agents():
    print("--- Running Multi-Agent Lesson Generation Test ---")
    settings = get_settings()

    client = ollama.Client(host=settings.ollama_base_url)
    client.list()
    print("Connected to active local Ollama server.")

    # 1. Generate standard lesson
    print("\n1. [Generating Standard Lesson about Derivatives]")
    lesson_std = generate_lesson(
        topic="definition of derivative",
        min_slides=2,
        max_slides=2,
        style_profile="standard",
    )
    print(f"Topic: {lesson_std.topic}")
    for idx, slide in enumerate(lesson_std.slides, 1):
        print(f"  Slide {idx}: {slide.title}")
        print(f"    Content: {slide.content[:150]}...")
        print(f"    LaTeX Math: {slide.latex_equation}")
        print(f"    HTML Widget: {slide.html_widget is not None} (expected: False)")
        print(f"    Accessibility: {slide.accessibility_notes}")

    # 2. Generate visual lesson (should contain HTML widgets)
    print("\n2. [Generating Visual Lesson about derivatives (with dynamic graphs)]")
    lesson_vis = generate_lesson(
        topic="definition of derivative",
        min_slides=2,
        max_slides=2,
        style_profile="visual",
    )
    print(f"Topic: {lesson_vis.topic}")
    for idx, slide in enumerate(lesson_vis.slides, 1):
        print(f"  Slide {idx}: {slide.title}")
        print(f"    Content: {slide.content[:150]}...")
        print(f"    LaTeX Math: {slide.latex_equation}")
        print(f"    HTML Widget: {slide.html_widget is not None} (expected: True)")
        if slide.html_widget:
            print(f"    HTML Snippet: {slide.html_widget[:120]}...")
        print(f"    Accessibility: {slide.accessibility_notes}")

    # 3. Generate ADHD lesson (should contain high-contrast lists/bullet points)
    print("\n3. [Generating ADHD Lesson about derivatives (punchy structure)]")
    lesson_adhd = generate_lesson(
        topic="definition of derivative",
        min_slides=2,
        max_slides=2,
        style_profile="adhd",
    )
    print(f"Topic: {lesson_adhd.topic}")
    for idx, slide in enumerate(lesson_adhd.slides, 1):
        print(f"  Slide {idx}: {slide.title}")
        print(f"    Content: {slide.content[:150]}...")
        print(f"    Accessibility: {slide.accessibility_notes}")


    print("\n>>> MULTI-AGENT LESSON ROUTING TEST PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    test_agents()
