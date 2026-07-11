"""Lightweight Gradio UI for manually exercising the PoliBot FastAPI backend.

Not part of the production system - just a dev-only front end for the
/query and /generate-exercise endpoints. Run the API first (uvicorn
polibot.api.main:app), then `python gradio_app.py`.
"""

import os
import tempfile
from pathlib import Path

import gradio as gr
import requests

API_URL = os.environ.get("POLIBOT_API_URL", "http://localhost:8000")


def ask(question: str, history: list[dict]) -> str:
    resp = requests.post(f"{API_URL}/query", json={"query": question})
    resp.raise_for_status()
    return resp.json()["answer"]


def generate_exercise_pdf(topic: str, count: int) -> str:
    resp = requests.post(
        f"{API_URL}/generate-exercise", json={"topic": topic, "count": int(count)}
    )
    resp.raise_for_status()
    pdf_path = Path(tempfile.gettempdir()) / f"{topic.replace(' ', '_') or 'exercises'}.pdf"
    pdf_path.write_bytes(resp.content)
    return str(pdf_path)


def generate_lesson_pdf(topic: str, min_slides: int, max_slides: int) -> str:
    resp = requests.post(
        f"{API_URL}/generate-lesson",
        json={"topic": topic, "min_slides": int(min_slides), "max_slides": int(max_slides)},
    )
    resp.raise_for_status()
    url = resp.json()["url"]
    return f"[Download lesson PDF]({url})"


with gr.Blocks(title="PoliBot Manual Testing") as demo:
    with gr.Tabs():
        with gr.Tab("Chat"):
            gr.ChatInterface(
                ask,
                type="messages",
                chatbot=gr.Chatbot(
                    type="messages",
                    latex_delimiters=[
                        {"left": "$$", "right": "$$", "display": True},
                        {"left": "$", "right": "$", "display": False},
                    ]
                ),
            )
        with gr.Tab("Generate Exercise"):
            topic_input = gr.Textbox(label="Topic")
            count_input = gr.Number(label="Number of exercises", value=1, precision=0)
            generate_btn = gr.Button("Generate")
            pdf_output = gr.File(label="Exercise PDF")
            generate_btn.click(
                generate_exercise_pdf, inputs=[topic_input, count_input], outputs=pdf_output
            )
        with gr.Tab("Generate Lesson"):
            lesson_topic_input = gr.Textbox(label="Topic")
            min_slides_input = gr.Number(label="Min slides", value=3, precision=0)
            max_slides_input = gr.Number(label="Max slides", value=6, precision=0)
            lesson_generate_btn = gr.Button("Generate")
            lesson_url_output = gr.Markdown(label="Bucket URL")
            lesson_generate_btn.click(
                generate_lesson_pdf,
                inputs=[lesson_topic_input, min_slides_input, max_slides_input],
                outputs=lesson_url_output,
            )

if __name__ == "__main__":
    demo.launch()
