from polibot.material_generation.exercises import Exercise, generate_exercise

def test_generate_exercise_returns_validated_pydantic_model_live():
    # Will hit the live LLM with actual RAG retrieval if there is any,
    # or just base LLM knowledge for 'algebra'.
    exercise = generate_exercise("algebra")

    assert isinstance(exercise, Exercise)
    assert exercise.statement is not None
    assert exercise.solution is not None

if __name__ == "__main__":
    test_generate_exercise_returns_validated_pydantic_model_live()
    print("ok")
