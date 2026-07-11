from dataclasses import dataclass, field

import fitz
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, TextNode


@dataclass
class Page:
    number: int
    text: str
    images: list[bytes] = field(default_factory=list)


def read_pdf(path: str) -> list[Page]:
    doc = fitz.open(path)
    pages = []
    for page in doc:
        images = [doc.extract_image(img[0])["image"] for img in page.get_images(full=True)]
        pages.append(Page(number=page.number + 1, text=page.get_text().strip(), images=images))
    doc.close()
    return pages


def chunk_pages(
    pages: list[Page],
    course: str,
    topic: str,
    chunk_size: int = 256,
    chunk_overlap: int = 50,
) -> list[TextNode]:
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    nodes: list[TextNode] = []
    for page in pages:
        if not page.text:
            continue
        document = Document(
            text=page.text,
            metadata={
                "course": course,
                "topic": topic,
                "page": page.number,
                "slide": page.number,
                "content_type": "text",
            },
        )
        # split per-page so a chunk never spans two slides; overlap only bleeds within a page
        nodes.extend(splitter.get_nodes_from_documents([document]))
    return nodes
