import re
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator

from polibot.generation.llm import generate_answer, reformulate_query
from polibot.material_generation.exercises import generate_exercise
from polibot.material_generation.lessons import generate_lesson, Slide
from polibot.material_generation.slide_editor import mutate_slide
from polibot.material_generation.exercise_fsm import start_exercise_session, evaluate_exercise_step
from polibot.material_generation.pdf_renderer import render_exercises_pdf, render_lesson_pdf
from polibot.retrieval.retriever import retrieve
from polibot.storage.materials import save_material
from polibot.storage.rustfs_client import get_presigned_url

app = FastAPI(title="PoliBot RAG API")


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    owner_id: str | None = None
    course_id: str | None = None


class ExerciseRequest(BaseModel):
    topic: str
    count: int = 1


class LessonRequest(BaseModel):
    topic: str
    min_slides: int = Field(gt=0)
    max_slides: int = Field(gt=0)
    style_profile: str = "standard"  # options: standard, visual, adhd, dyslexia

    @model_validator(mode="after")
    def check_slide_range(self):
        if self.min_slides > self.max_slides:
            raise ValueError("min_slides must be <= max_slides")
        return self


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query(request: QueryRequest):
    reformulated = reformulate_query(request.query)
    nodes = retrieve(
        reformulated,
        top_k=request.top_k,
        owner_id=request.owner_id,
        course_id=request.course_id,
    )

    sources = [{"text": n.node.get_content(), "metadata": n.node.metadata} for n in nodes]
    answer = generate_answer(request.query, sources)

    return {
        "answer": answer,
        "sources": [
            {"index": i, "score": n.score, **n.node.metadata} for i, n in enumerate(nodes, start=1)
        ],
    }


@app.post("/exercises")
def exercises(request: ExerciseRequest):
    return {"exercises": [generate_exercise(request.topic) for _ in range(request.count)]}


@app.post("/generate-exercise")
def generate_exercise_pdf(request: ExerciseRequest):
    generated = [generate_exercise(request.topic) for _ in range(request.count)]
    pdf_path = Path(tempfile.mkdtemp()) / "exercises.pdf"
    render_exercises_pdf(request.topic, generated, pdf_path)

    material = save_material(
        pdf_path=str(pdf_path),
        author="PoliBot Agent System",
        course="PoliTO Course",
        topic=request.topic,
    )

    return {"url": get_presigned_url(material.key), "id": material.id}


@app.post("/generate-lesson")
def generate_lesson_pdf(request: LessonRequest):
    lesson = generate_lesson(
        request.topic,
        request.min_slides,
        request.max_slides,
        style_profile=request.style_profile,
    )
    pdf_path = Path(tempfile.mkdtemp()) / "lesson.pdf"
    render_lesson_pdf(lesson, pdf_path)

    material = save_material(
        pdf_path=str(pdf_path),
        author="PoliBot Agent System",
        course="PoliTO Course",
        topic=request.topic,
    )

    return {"url": get_presigned_url(material.key), "key": material.key, "id": material.id}


class SlideEditRequest(BaseModel):
    slide: Slide
    instruction: str
    course_id: str | None = None


@app.post("/edit-slide")
def edit_slide(request: SlideEditRequest):
    updated_slide = mutate_slide(request.slide, request.instruction, request.course_id)
    return {"slide": updated_slide}


class StartExerciseRequest(BaseModel):
    topic: str
    student_id: str


class EvaluateStepRequest(BaseModel):
    session_id: str
    user_input: str


@app.post("/exercises/start")
def start_exercise(request: StartExerciseRequest):
    return start_exercise_session(request.topic, request.student_id)


@app.post("/exercises/step")
def evaluate_step(request: EvaluateStepRequest):
    return evaluate_exercise_step(request.session_id, request.user_input)
