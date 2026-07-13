import ollama
from polibot.config import get_settings
from polibot.material_generation.exercise_fsm import (
    start_exercise_session,
    evaluate_exercise_step,
)
from polibot.storage.postgres import SessionLocal
from polibot.storage.models import StudentError


def run_fsm_simulation():
    print("--- Running Guided Exercise FSM Walkthrough ---")
    settings = get_settings()

    print("Connected to active local PostgreSQL & Ollama servers.")
    # 1. Start the exercise
    student_id = "student_401"
    topic = "maximum area optimization"
    print("\n1. [Starting Guided Optimization Exercise]")
    session = start_exercise_session(topic, student_id)
    session_id = session["session_id"]
    print(f"Session Started: ID={session_id}")
    print(f"Step 1 Prompt: {session['step_description']}")

    # 2. Submit CORRECT step 1 answer
    print("\n2. [Submitting CORRECT Answer for Step 1]")
    user_input_1 = "The objective function for the area of a rectangle is A(x) = x * y."
    result_1 = evaluate_exercise_step(session_id, user_input_1)
    print(f"Result status: {result_1['status']}")
    if "step_description" in result_1:
        print(f"Next Step: {result_1['step_description']}")

    assert result_1["status"] == "CORRECT", "Step 1 should be graded CORRECT"

    # 3. Submit INCORRECT step 2 answer (should generate hint and log error)
    print("\n3. [Submitting INCORRECT Answer for Step 2 (modeling constraints)]")
    user_input_2_bad = "The perimeter constraint is yellow because the sun is hot, so x + y = banana."
    result_2_bad = evaluate_exercise_step(session_id, user_input_2_bad)
    print(f"Result status: {result_2_bad['status']}")
    print(f"Generated Hint: {result_2_bad.get('hint')}")
    print(f"Skill Tagged: {result_2_bad.get('skill_type')}")

    print("Result status:", result_2_bad.get("status"))
    print("Generated Hint:", result_2_bad.get("hint"))
    print("Skill Tagged:", result_2_bad.get("skill_id"))

    # Now let's try step 2 CORRECTLY
    # 4. Submit CORRECT step 2 answer
    print("\n4. [Submitting CORRECT Answer for Step 2]")
    user_input_2_good = "Given a perimeter of 200, 2x + 2y = 200, so y = 100 - x."
    result_2_good = evaluate_exercise_step(session_id, user_input_2_good)
    print(f"Result status: {result_2_good['status']}")
    if "step_description" in result_2_good:
        print(f"Next Step: {result_2_good['step_description']}")

    # 5. Submit CORRECT step 3 answer
    print("\n5. [Submitting CORRECT Answer for Step 3]")
    user_input_3 = "The derivative A'(x) = 100 - 2x = 0, so the critical point is x = 25."
    result_3 = evaluate_exercise_step(session_id, user_input_3)
    print(f"Result status: {result_3['status']}")
    if "step_description" in result_3:
        print(f"Next Step: {result_3['step_description']}")

    # 6. Submit CORRECT step 4 answer to complete
    print("\n6. [Submitting CORRECT Answer for Step 4 (boundary checking)]")
    user_input_4 = "Evaluating boundaries, the maximum area is 1250 at x = 25."
    result_4 = evaluate_exercise_step(session_id, user_input_4)
    print(f"Result status: {result_4['status']}")
    print(f"Message: {result_4.get('message')}")
    print(f"Completed: {result_4.get('completed')}")

    assert result_4.get("completed") is True

    # 7. Check database log for the error
    print("\n7. [Verifying Error Analytics Log in PostgreSQL]")
    with SessionLocal() as db_session:
        errors = (
            db_session.query(StudentError)
            .filter(StudentError.student_id == student_id)
            .all()
        )
        print(f"Found {len(errors)} error logs in database for student '{student_id}':")
        for err in errors:
            print(
                f"  - ID: {err.id}, Skill: {err.skill_type}, Detail: {err.error_message}"
            )

        assert len(errors) > 0, "The incorrect step 2 should be logged in PostgreSQL!"

    print("\n>>> GUIDED EXERCISE STATE MACHINE WALKTHROUGH PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    run_fsm_simulation()
