import base64

import ollama

from polibot.config import get_settings
from polibot.ingestion.chunking import Page

CAPTION_PROMPT = (
    "Describe this diagram or image in detail, focusing on any text, "
    "labels, and concepts it conveys."
)


def caption_image(image_bytes: bytes) -> str:
    settings = get_settings()
    client = ollama.Client(host=settings.ollama_base_url)
    response = client.generate(
        model=settings.ollama_vlm_model,
        prompt=CAPTION_PROMPT,
        images=[base64.b64encode(image_bytes).decode("utf-8")],
    )
    return response["response"].strip()


def caption_page_images(page: Page) -> list[str]:
    return [caption_image(image_bytes) for image_bytes in page.images]
