from unittest.mock import MagicMock, patch

from polibot.generation.llm import generate_answer, reformulate_query


def test_reformulate_query_falls_back_to_original_when_empty():
    fake_client = MagicMock()
    fake_client.generate.return_value = {"response": "   "}
    with patch("polibot.generation.llm.ollama.Client", return_value=fake_client):
        result = reformulate_query("what is recursion")
    assert result == "what is recursion"


def test_generate_answer_numbers_sources_and_includes_metadata():
    fake_client = MagicMock()
    fake_client.generate.return_value = {"response": "Recursion is [1]."}
    sources = [
        {
            "text": "Recursion calls itself.",
            "metadata": {"course": "CS101", "topic": "recursion", "slide": 4},
        }
    ]
    with patch("polibot.generation.llm.ollama.Client", return_value=fake_client):
        answer = generate_answer("What is recursion?", sources)

    assert answer == "Recursion is [1]."
    prompt = fake_client.generate.call_args.kwargs["prompt"]
    assert "[1]" in prompt
    assert "CS101" in prompt
    assert "Recursion calls itself." in prompt


if __name__ == "__main__":
    test_reformulate_query_falls_back_to_original_when_empty()
    test_generate_answer_numbers_sources_and_includes_metadata()
    print("ok")
