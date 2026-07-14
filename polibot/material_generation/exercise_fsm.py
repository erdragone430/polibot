import uuid
import json
import ollama
from pydantic import BaseModel
from polibot.config import get_settings
from polibot.storage.models import StudentError
from polibot.storage.postgres import SessionLocal, ensure_tables

# In-memory session store for active exercise attempts
ACTIVE_SESSIONS = {}

STEPS_METADATA = [
    {
        "index": 1,
        "description": "Step 1: Set up the objective function (algebraic model of the problem targets).",
        "solution_key": "A(x) = x * y",
        "skill_type": "algebra_setup",
    },
    {
        "index": 2,
        "description": "Step 2: Model the constraint equations and reduce the objective function to a single variable.",
        "solution_key": "y = 100 - 2x",
        "skill_type": "constraint_modeling",
    },
    {
        "index": 3,
        "description": "Step 3: Perform differential operations to find the derivative and critical zeros (solve A'(x) = 0).",
        "solution_key": "x = 25",
        "skill_type": "differential_operations",
    },
    {
        "index": 4,
        "description": "Step 4: Check boundaries and endpoints to determine the global optimum.",
        "solution_key": "maximum area is 1250",
        "skill_type": "boundary_check",
    },
]

EVAL_PROMPT = (
    "You are a math grading tutor. Grade the student's answer for Step {step_index}.\n"
    "Step Description: {step_desc}\n"
    "Expected Solution: {solution_key}\n"
    "Student's Answer: {user_input}\n\n"
    "Analyze if the student's response is mathematically and conceptually correct.\n"
    "If it is correct, output EXACTLY the word: CORRECT\n"
    "Otherwise, generate a brief, helpful hint pointing out the mistake without giving away the exact answer. "
    "Classify the error under the skill: '{skill_type}'.\n"
    "Output your response strictly in this JSON format:\n"
    "{{\n"
    "  \"status\": \"INCORRECT\",\n"
    "  \"hint\": \"your brief hint here\",\n"
    "  \"skill_type\": \"{skill_type}\"\n"
    "}}"
)


class ActiveExercise(BaseModel):
    session_id: str
    student_id: str
    topic: str
    current_step: int = 1


def start_exercise_session(topic: str, student_id: str) -> dict:
    ensure_tables()
    session_id = str(uuid.uuid4())
    ACTIVE_SESSIONS[session_id] = ActiveExercise(
        session_id=session_id, student_id=student_id, topic=topic, current_step=1
    )

    first_step = STEPS_METADATA[0]
    return {
        "session_id": session_id,
        "topic": topic,
        "current_step": 1,
        "step_description": first_step["description"],
    }


def evaluate_exercise_step(session_id: str, user_input: str) -> dict:
    session = ACTIVE_SESSIONS.get(session_id)
    if not session:
        return {"error": "Invalid session ID"}

    step_idx = session.current_step
    if step_idx > len(STEPS_METADATA):
        return {"message": "Exercise already completed!", "completed": True}

    step_info = STEPS_METADATA[step_idx - 1]

    settings = get_settings()
    client = ollama.Client(host=settings.ollama_base_url)

    response = client.generate(
        model=settings.ollama_reformulation_model,  # use smaller model for fast grading
        prompt=EVAL_PROMPT.format(
            step_index=step_idx,
            step_desc=step_info["description"],
            solution_key=step_info["solution_key"],
            user_input=user_input,
            skill_type=step_info["skill_type"],
        ),
    )

    raw_response = response["response"].strip()

    if "CORRECT" in raw_response:
        # Move to next step
        session.current_step += 1
        if session.current_step > len(STEPS_METADATA):
            return {
                "status": "CORRECT",
                "message": "Excellent work! You have completed the guided exercise.",
                "completed": True,
            }
        else:
            next_step = STEPS_METADATA[session.current_step - 1]
            return {
                "status": "CORRECT",
                "message": "Correct! Moving to the next step.",
                "next_step": session.current_step,
                "step_description": next_step["description"],
                "completed": False,
            }
    else:
        # Parse error JSON
        hint = "Check your calculations."
        skill_type = step_info["skill_type"]
        try:
            # find JSON segment
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            if start != -1 and end != 0:
                parsed = json.loads(raw_response[start:end])
                hint = parsed.get("hint", hint)
                skill_type = parsed.get("skill_type", skill_type)
        except Exception:
            pass

        # Log error to database
        with SessionLocal() as db_session:
            err = StudentError(
                student_id=session.student_id,
                exercise_id=session.topic,
                step_index=step_idx,
                skill_type=skill_type,
                error_message=f"Input: '{user_input}'. Hint generated: '{hint}'",
            )
            db_session.add(err)
            db_session.commit()

        return {
            "status": "INCORRECT",
            "hint": hint,
            "skill_type": skill_type,
            "completed": False,
        }
