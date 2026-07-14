# PoliBot

## Introduction

This project is the result of work assigned as part of a research grant with the Politecnico di Torino (PoliTO). The team's task was to demonstrate a prototype of an agent integrable with the PoliTO course channels, capable of helping students with their studies.

The part I was responsible for was defining the entire RAG (Retrieval-Augmented Generation) architecture of the system, together with designing and implementing the new-material-generation component (exercises and personalized lessons) based on the course content.

The current project is an MVP (Minimum Viable Product): the goal is to demonstrate the technical feasibility of the proposed architecture, not to deliver a production-ready system.Some choices described in this document (authentication, permission handling, scalability) are simplified compared to what a real deployment with active students would require.

## What the project does

PoliBot is a system that, starting from a course's material (slide decks in PDF), allows:

1. **Answering student questions** about the course content, citing the specific sources (slide, page, topic) the answer comes from, reducing the risk of made-up answers (hallucination). Retrieval is multi-tenant aware: results can be scoped to a course and to a mix of public material plus a specific student's own private notes, with no cross-student leakage.
2. **Generating new exercises** on a requested topic, based on the style and structure of exercises already present in the course material, but with different data or scenarios.
3. **Generating personalized lessons** on a specific topic, with a configurable number of slides within a user-defined minimum/maximum range, optionally tailored to an accessibility profile (`standard`, `visual`, `adhd`, `dyslexia`) that adjusts content structure and can attach a self-contained interactive HTML widget per slide.
4. **Editing a previously generated slide** through a natural-language instruction (e.g. "shorten this and add a warning about X"), re-grounded in course context retrieved for that instruction.
5. **Running a guided, step-by-step exercise session**: the student submits an answer for each step of a fixed multi-step problem, an LLM grades it as correct/incorrect and returns a hint on failure, and incorrect attempts are logged to PostgreSQL tagged by skill type, for later analysis of common mistakes.
6. **Storing generated lessons** as PDF files in centralized object storage (RustFS) with the material indexed in PostgreSQL, made accessible via a direct URL. Generated exercises are returned directly as a PDF and are not persisted.

## Architecture

The system is organized into two main flows, which share the same underlying infrastructure (vector database, embedding models).

### 1. RAG Flow (Questions and Answers)

The pipeline is split into an offline phase and an online phase.

**Offline phase (ingestion, run once or whenever the course material is updated):**

- Course slides (PDF) are read and split into chunks at the slide/page level, using a semantic chunking strategy with a 50-token overlap between contiguous chunks, to preserve continuity of concepts across related slides.
- Images and diagrams present in the slides are described through a vision-language model (captioning), and the resulting textual caption is treated as a regular text chunk.
- Each chunk (text and caption) is transformed into a dense vector, and a sparse vector is also generated for keyword-based search.
- The vectors (dense and sparse) are stored in Qdrant, together with associated metadata (course, slide, page, topic).

**Online phase (run for each student query):**

1. **Query reformulation**: the raw student question is rewritten by a small local model before retrieval, to improve match quality against the indexed chunks.
2. **Embedding**: the reformulated question is transformed into a vector using the same model used during ingestion.
3. **Retrieval**: a hybrid search is performed on Qdrant, combining similarity search (dense vectors) and keyword search (sparse vectors), fusing the results with Reciprocal Rank Fusion (RRF). An optional Qdrant payload filter restricts candidates to a given `course_id`, and to chunks whose `access_scope` is `public` or whose `owner_id` matches the requesting student — enforcing multi-tenant isolation of private material at the retrieval layer.
4. **Reranking**: the top candidates are reordered by a dedicated reranking model (a cross-encoder), which evaluates the relevance of each chunk to the query more precisely than similarity search alone.
5. **Augmentation**: the most relevant chunks, together with their metadata, are inserted into a structured prompt sent to the generative model, with explicit instructions to answer only based on the provided material.
6. **Output**: the model generates the final answer, citing the sources the information comes from.

### 2. Material Generation Flow (Exercises and Lessons)

This flow reuses the same retrieval infrastructure as the RAG flow, adapted to a generative task rather than question answering.

1. **Template Retrieval**: given a topic requested by the student, the system retrieves similar exercises or content already present in the course material, which serve as reference templates for style, notation, and difficulty.
2. **Generation**: a dedicated prompt guides the model to generate new content (an exercise, or a lesson's slides) while preserving the structure of the retrieved examples, but with different data or topics. The output is constrained to a structured schema (Pydantic), ensuring the result is always in a predictable, usable format (statement, data, solution for exercises; title, content, LaTeX equation, optional HTML widget, and accessibility notes for each lesson slide). For lessons, generation is driven by a requested `style_profile` (`standard`, `visual`, `adhd`, `dyslexia`) that shapes content structure and whether a self-contained interactive HTML widget is attached to a slide.
3. **PDF Rendering**: the structured content is turned into an actual PDF document, through a LaTeX template filled by a templating engine (Jinja2) and compiled with pdflatex. This approach ensures correct rendering of mathematical notation, which is common in a technical course's material.
4. **Storage**: for lessons, the generated PDF is uploaded to S3-compatible storage (RustFS) and indexed as a `Material` row in PostgreSQL; a direct URL and the material's id are returned to the caller. Generated exercises are returned as a PDF response directly and are not uploaded anywhere.
5. **Slide editing**: an already-generated slide can be revised via a free-text instruction; the instruction plus the slide's own title/content are used to retrieve fresh course context, which is fed back to the model together with the original slide JSON to produce an updated slide matching the same schema.

### 3. Guided Exercise Session (Math Solver FSM)

A separate flow lets a student work through a fixed multi-step problem interactively rather than receiving a finished exercise PDF:

1. **Start**: a session is created (in-memory, keyed by a UUID) for a student and topic, returning the description of the first step.
2. **Step evaluation**: for each submitted answer, a grading model (the small reformulation model, for low latency) judges it against the expected result for that step and returns either `CORRECT` (advancing to the next step) or `INCORRECT` with a hint and a `skill_type` tag, without revealing the answer.
3. **Error logging**: every incorrect attempt is persisted to PostgreSQL (`StudentError`: student, exercise, step index, skill type, error detail), building a dataset of where students actually struggle, per skill.

**Note**: the current step content/solutions are a single hardcoded four-step optimization problem (`STEPS_METADATA` in `exercise_fsm.py`), independent of the `topic` passed at session start — this is a prototype stand-in for a future topic-driven step generator.

## Models Used

The system uses several models, each for a specific task, through Ollama:

| Model | Role | Execution |
|---|---|---|
| `nomic-embed-text` | Text embedding (chunks and queries) | Local |
| `gemma2:2b` | Query reformulation; final answer generation for Q&A; exercise and lesson generation (structured output); guided-exercise step grading | Local |
| `moondream` | Image/diagram captioning (vision-language model) | Local |
| `bge-reranker-v2-m3` | Reranking of retrieval results | Local |

**Note**: exercise generation includes a JSON-repair step, since the lesson/exercise model doesn't always honor the structured output schema constraint on the first attempt: malformed responses are patched (e.g. fixing unescaped LaTeX backslashes) and, if still invalid, re-generated via the same `gemma2:2b` model used for query reformulation, which honors the schema more reliably. All LLM inference (Q&A, captioning, exercise/lesson generation, slide editing, step grading) runs locally via Ollama, with no cloud model dependency.

## Technology Stack

- **RAG Framework**: LlamaIndex
- **Vector database**: Qdrant (with native support for dense and sparse vectors)
- **Relational database**: PostgreSQL (generated-material index; guided-exercise student error log)
- **Object storage**: RustFS (S3-compatible, written in Rust)
- **Backend**: FastAPI
- **Test UI**: Gradio
- **LLM models**: Ollama (local only)
- **PDF rendering**: Jinja2 + LaTeX (pdflatex)
- **Dependency management**: Poetry

## Deployment

### Prerequisites

- Docker and Docker Compose
- Python 3.11 or 3.12 (3.13+ not supported yet) and Poetry
- A LaTeX distribution (for PDF rendering):
  ```bash
  sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra
  ```
- Ollama installed and running locally

### 1. Environment configuration

Copy the example file and fill it in with your own values:

```bash
cp .env.example .env
```

In particular, set:
- `POSTGRES_PASSWORD` and `RUSTFS_SECRET_KEY`: generate secure values with `openssl rand -hex 32` instead of leaving the placeholders

### 2. Start the infrastructure services

```bash
docker-compose up -d
docker-compose ps   # verify Qdrant, PostgreSQL, and RustFS are "Up"
```

### 3. Download the local models

```bash
ollama pull nomic-embed-text
ollama pull gemma2:2b
ollama pull moondream
```

### 4. Install Python dependencies

```bash
poetry install
```

### 5. Ingest the course material

Place the slide PDFs in a dedicated folder, then run:

```bash
poetry run python -m polibot.ingestion.run --source <pdf_folder_path> --course <course_name>
```

Verify that ingestion succeeded by checking that the Qdrant collection is not empty:

```bash
curl http://localhost:6333/collections/polibot
```

### 6. Start the backend

```bash
poetry run uvicorn polibot.api.main:app --reload
```

The backend will be reachable at `http://localhost:8000` (interactive docs at `http://localhost:8000/docs`).

### 7. Start the test interface

In a second terminal:

```bash
poetry run python gradio_app.py
```

The interface will be reachable at `http://127.0.0.1:7860`, with three sections: Chat (questions and answers), Generate Exercise (exercise generation), and Generate Lesson (personalized lesson generation). Multi-tenant retrieval, slide editing, and the guided-exercise FSM are only exposed via the API (`/query`, `/edit-slide`, `/exercises/start`, `/exercises/step`) for now, not yet wired into this test UI.

## Known Limitations (MVP)

- The storage bucket is currently configured with public read access, for simplicity of local testing; a real deployment should protect it with presigned URLs or authentication.
- Captioning images in the slides is a slow operation (roughly one minute per image, on the local model used); full ingestion with captioning enabled may take a long time on courses with many images.
- There is no end-user (student) authentication mechanism; `owner_id`/`student_id` are passed as plain request fields and trusted as-is, so the multi-tenant retrieval filter and the exercise FSM's error log are not protected against a client claiming another student's id. The system is intended to be integrated in the future into the official PoliTO course channel, which will handle this aspect.
- All inference now runs on small local models (`gemma2:2b` for text, `moondream` for captioning) instead of a larger cloud model; answer quality and reasoning depth may be more limited than what a larger cloud model would provide. This is a deliberate speed/simplicity trade-off for the MVP.
- Guided-exercise (FSM) sessions are held in an in-memory dict (`ACTIVE_SESSIONS`), so they don't survive an API restart and don't work across multiple backend replicas; the step content itself is a single hardcoded problem, not yet generated per topic.
