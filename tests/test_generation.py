from polibot.generation.llm import generate_answer, reformulate_query

def test_reformulate_query_works_live():
    result = reformulate_query("what is recursion")
    assert "recursion" in result.lower()

def test_generate_answer_uses_context_live():
    sources = [
        {
            "text": "Recursion calls itself. The base case is crucial.",
            "metadata": {"course": "CS101", "topic": "recursion", "slide": 4},
        }
    ]
    answer = generate_answer("What is recursion?", sources)

    assert len(answer) > 0
    # It should mention something from the source text
    assert "call" in answer.lower() or "base case" in answer.lower() or "itself" in answer.lower()

if __name__ == "__main__":
    test_reformulate_query_works_live()
    test_generate_answer_uses_context_live()
    print("ok")
