from polibot.material_generation.lessons import Lesson, generate_lesson

def test_generate_lesson_uses_local_client_and_returns_validated_model_live():
    # Calling the LLM directly with RAG (or standard knowledge if none exists)
    lesson = generate_lesson("recursion", min_slides=1, max_slides=2)

    assert isinstance(lesson, Lesson)
    assert lesson.topic is not None
    assert len(lesson.slides) >= 1

if __name__ == "__main__":
    test_generate_lesson_uses_local_client_and_returns_validated_model_live()
    print("ok")
