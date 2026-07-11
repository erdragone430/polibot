# PoliBot

## Introduction

This project is the result of work assigned as part of a research grant with the Politecnico di Torino (PoliTO). The team's task was to demonstrate a prototype of an agent integrable with the PoliTO course channels, capable of helping students with their studies.

The part I was responsible for was defining the entire RAG (Retrieval-Augmented Generation) architecture of the system, together with designing and implementing the new-material-generation component (exercises and personalized lessons) based on the course content.

The current project is an MVP (Minimum Viable Product): the goal is to demonstrate the technical feasibility of the proposed architecture, not to deliver a production-ready system.Some choices described in this document (authentication, permission handling, scalability) are simplified compared to what a real deployment with active students would require.

## What the project does

PoliBot is a system that, starting from a course's material (slide decks in PDF), allows:

1. **Answering student questions** about the course content, citing the specific sources (slide, page, topic) the answer comes from, reducing the risk of made-up answers (hallucination).
2. **Generating new exercises** on a requested topic, based on the style and structure of exercises already present in the course material, but with different data or scenarios.
3. **Generating personalized lessons** on a specific topic, with a configurable number of slides within a user-defined minimum/maximum range.
4. **Storing generated lessons** as PDF files in centralized object storage, made accessible via a direct URL. (Generated exercises are returned directly as a PDF and are not currently persisted; a Postgres-backed material index exists in the codebase but isn't wired into the API yet.)

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

1. **Reformulation**: the student's question is cleaned and reformulated by a lightweight model, resolving ambiguity or implicit terms before the search.
2. **Embedding**: the reformulated question is transformed into a vector using the same model used during ingestion.
3. **Retrieval**: a hybrid search is performed on Qdrant, combining similarity search (dense vectors) and keyword search (sparse vectors), fusing the results with Reciprocal Rank Fusion (RRF).
4. **Reranking**: the top candidates are reordered by a dedicated reranking model (a cross-encoder), which evaluates the relevance of each chunk to the query more precisely than similarity search alone.
5. **Augmentation**: the most relevant chunks, together with their metadata, are inserted into a structured prompt sent to the generative model, with explicit instructions to answer only based on the provided material.
6. **Output**: the model generates the final answer, citing the sources the information comes from.

### 2. Material Generation Flow (Exercises and Lessons)

This flow reuses the same retrieval infrastructure as the RAG flow, adapted to a generative task rather than question answering.

1. **Template Retrieval**: given a topic requested by the student, the system retrieves similar exercises or content already present in the course material, which serve as reference templates for style, notation, and difficulty.
2. **Generation**: a dedicated prompt guides the model to generate new content (an exercise, or a lesson's slides) while preserving the structure of the retrieved examples, but with different data or topics. The output is constrained to a structured schema (Pydantic), ensuring the result is always in a predictable, usable format (statement, data, solution for exercises; title and content for each lesson slide).
3. **PDF Rendering**: the structured content is turned into an actual PDF document, through a LaTeX template filled by a templating engine (Jinja2) and compiled with pdflatex. This approach ensures correct rendering of mathematical notation, which is common in a technical course's material.
4. **Storage**: for lessons, the generated PDF is uploaded to S3-compatible storage (a bucket) and a direct URL is returned to the caller. Generated exercises are returned as a PDF response directly and are not uploaded anywhere.

## Models Used

The system uses several models, each for a specific task, through Ollama:

| Model | Role | Execution |
|---|---|---|
| `bge-m3` | Text embedding (chunks and queries) | Local |
| `llava` | Image/diagram captioning | Local |
| `gemma4:e2b` | User query reformulation; JSON-repair fallback for exercise generation | Local |
| `gemma4:e4b` | Lesson generation (structured output) | Local |
| `gemma4:31b` | Final answer generation for Q&A; exercise generation (structured output) | Ollama Cloud |
| `bge-reranker-v2-m3` | Reranking of retrieval results | Local |

**Important technical note**: during development, it emerged that the cloud model (`gemma4:31b`) does not reliably honor structured output constraints (JSON schema), unlike local execution. Lesson generation avoids this entirely by using the local `gemma4:e4b` model. Exercise generation still calls the cloud model first (for quality), and works around its unreliable structured output with a JSON-repair step: malformed responses are patched (e.g. fixing unescaped LaTeX backslashes) and, if still invalid, repaired by the local `gemma4:e2b` model, which honors the schema reliably.

## Technology Stack

- **RAG Framework**: LlamaIndex
- **Vector database**: Qdrant (with native support for dense and sparse vectors)
- **Relational database**: PostgreSQL (material metadata/index — schema and persistence code exist but aren't yet called from the API)
- **Object storage**: RustFS (S3-compatible, written in Rust)
- **Backend**: FastAPI
- **Test UI**: Gradio
- **LLM models**: Ollama (local and cloud)
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
- An Ollama Cloud API key (free), obtainable at https://ollama.com/settings/keys

### 1. Environment configuration

Copy the example file and fill it in with your own values:

```bash
cp .env.example .env
```

In particular, set:
- `OLLAMA_API_KEY`: your Ollama Cloud key
- `POSTGRES_PASSWORD` and `RUSTFS_SECRET_KEY`: generate secure values with `openssl rand -hex 32` instead of leaving the placeholders

### 2. Start the infrastructure services

```bash
docker-compose up -d
docker-compose ps   # verify Qdrant, PostgreSQL, and RustFS are "Up"
```

### 3. Download the local models

```bash
ollama pull bge-m3
ollama pull llava
ollama pull gemma4:e2b
ollama pull gemma4:e4b
```

The `gemma4:31b` model does not need to be downloaded: it is called via Ollama Cloud using the key configured in `OLLAMA_API_KEY`.

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

The interface will be reachable at `http://127.0.0.1:7860`, with three sections: Chat (questions and answers), Generate Exercise (exercise generation), and Generate Lesson (personalized lesson generation).

## Known Limitations (MVP)

- The storage bucket is currently configured with public read access, for simplicity of local testing; a real deployment should protect it with presigned URLs or authentication.
- Captioning images in the slides is a slow operation (roughly one minute per image, on the local model used); full ingestion with captioning enabled may take a long time on courses with many images.
- There is no end-user (student) authentication mechanism; the system is intended to be integrated in the future into the official PoliTO course channel, which will handle this aspect.
