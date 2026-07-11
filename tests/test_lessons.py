from unittest.mock import MagicMock, patch

import pytest

from polibot.material_generation.lessons import Lesson, generate_lesson


def _fake_node(text: str) -> MagicMock:
    node = MagicMock()
    node.node.get_content.return_value = text
    return node


def test_generate_lesson_uses_local_client_and_returns_validated_model():
    fake_client = MagicMock()
    fake_client.generate.return_value = {
        "response": (
            '{"topic": "recursion", "slides": ['
            '{"title": "Intro", "content": "What is recursion?"},'
            '{"title": "Base case", "content": "Every recursive call needs one."}'
            "]}"
        )
    }
    with (
        patch(
            "polibot.material_generation.lessons.retrieve",
            return_value=[_fake_node("existing lesson slide")],
        ),
        patch(
            "polibot.material_generation.lessons.ollama.Client", return_value=fake_client
        ) as fake_ollama_client,
    ):
        lesson = generate_lesson("recursion", min_slides=2, max_slides=4)

    assert isinstance(lesson, Lesson)
    assert lesson.topic == "recursion"
    assert len(lesson.slides) == 2
    assert lesson.slides[0].title == "Intro"

    # must use the local client, not the cloud client, since cloud ignores `format`
    fake_ollama_client.assert_called_once()
    called_kwargs = fake_client.generate.call_args.kwargs
    assert called_kwargs["format"] == Lesson.model_json_schema()


def test_generate_lesson_raises_on_malformed_llm_output():
    fake_client = MagicMock()
    fake_client.generate.return_value = {"response": "not json"}
    with (
        patch("polibot.material_generation.lessons.retrieve", return_value=[]),
        patch("polibot.material_generation.lessons.ollama.Client", return_value=fake_client),
        pytest.raises(ValueError),
    ):
        generate_lesson("recursion", min_slides=2, max_slides=4)


if __name__ == "__main__":
    test_generate_lesson_uses_local_client_and_returns_validated_model()
    test_generate_lesson_raises_on_malformed_llm_output()
    print("ok")
