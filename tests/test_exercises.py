from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from polibot.material_generation.exercises import Exercise, generate_exercise


def _fake_node(text: str) -> MagicMock:
    node = MagicMock()
    node.node.get_content.return_value = text
    return node


def test_generate_exercise_returns_validated_pydantic_model():
    fake_client = MagicMock()
    fake_client.generate.return_value = {
        "response": '{"statement": "Solve for x: 2x=10", "data": {"a": 2, "b": 10}, "solution": "x=5"}'
    }
    with (
        patch(
            "polibot.material_generation.exercises.retrieve",
            return_value=[_fake_node("existing exercise")],
        ),
        patch(
            "polibot.material_generation.exercises.ollama.Client", return_value=fake_client
        ),
    ):
        exercise = generate_exercise("algebra")

    assert isinstance(exercise, Exercise)
    assert exercise.solution == "x=5"
    assert exercise.data == {"a": 2, "b": 10}


def test_generate_exercise_raises_on_malformed_llm_output():
    fake_client = MagicMock()
    fake_client.generate.return_value = {"response": "not json"}
    with (
        patch("polibot.material_generation.exercises.retrieve", return_value=[]),
        patch("polibot.material_generation.exercises.ollama.Client", return_value=fake_client),
        pytest.raises(ValidationError),
    ):
        generate_exercise("algebra")


if __name__ == "__main__":
    test_generate_exercise_returns_validated_pydantic_model()
    test_generate_exercise_raises_on_malformed_llm_output()
    print("ok")
