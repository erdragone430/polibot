import re
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from polibot.generation.llm import generate_answer
from polibot.material_generation.exercises import generate_exercise
from polibot.material_generation.lessons import generate_lesson
from polibot.material_generation.pdf_renderer import render_exercises_pdf, render_lesson_pdf
from polibot.retrieval.retriever import retrieve
from polibot.storage.rustfs_client import upload_file

app = FastAPI(title="PoliBot RAG API")


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class ExerciseRequest(BaseModel):
    topic: str
    count: int = 1


class LessonRequest(BaseModel):
    topic: str
    min_slides: int = Field(gt=0)
    max_slides: int = Field(gt=0)

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
    nodes = retrieve(request.query, top_k=request.top_k)

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
    return FileResponse(pdf_path, media_type="application/pdf", filename="exercises.pdf")


@app.post("/generate-lesson")
def generate_lesson_pdf(request: LessonRequest):
    lesson = generate_lesson(request.topic, request.min_slides, request.max_slides)
    pdf_path = Path(tempfile.mkdtemp()) / "lesson.pdf"
    render_lesson_pdf(lesson, pdf_path)

    key = f"lessons/{slugify(request.topic)}/{uuid.uuid4()}.pdf"
    url = upload_file(str(pdf_path), key)

    return {"url": url, "key": key}
