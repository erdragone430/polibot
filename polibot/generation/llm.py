import ollama

from polibot.config import get_settings

REFORMULATION_PROMPT = (
    "Rewrite the user's question into a clear, specific search query for retrieving "
    "course slide content. Output only the rewritten query, nothing else.\n\n"
    "Question: {query}"
)

ANSWER_SYSTEM_PROMPT = (
    "You are a course assistant. Answer the question using only the numbered sources "
    "below. Cite sources inline using their number in square brackets, e.g. [1]. "
    "If the sources don't contain the answer, say so."
)


def reformulate_query(query: str) -> str:
    settings = get_settings()
    client = ollama.Client(host=settings.ollama_base_url)
    response = client.generate(
        model=settings.ollama_reformulation_model,
        prompt=REFORMULATION_PROMPT.format(query=query),
    )
    return response["response"].strip() or query


def generate_answer(query: str, sources: list[dict]) -> str:
    """sources: [{"text": ..., "metadata": {...}}, ...] in citation order."""
    settings = get_settings()
    client = ollama.Client(host=settings.ollama_base_url)

    # format context fragments with XML-like structure
    context_fragments = ""
    for i, s in enumerate(sources, start=1):
        metadata_str = f"Source [{i}] - Course: {s['metadata'].get('course')}, Slide/Page: {s['metadata'].get('slide')}, Topic: {s['metadata'].get('topic')}"
        context_fragments += f"\n--- {metadata_str} ---\n{s['text']}\n"

    prompt = (
        "<instruction>\n"
        "You are an advanced, factually rigid AI teaching assistant for Politecnico di Torino.\n"
        "Answer the user query using ONLY the verified text context fragments provided below. \n"
        "If the context does not contain sufficient mathematical or logical grounds to answer, "
        "state clearly that the information is unavailable in the material. Do not hallucinate.\n"
        "Cite the source file and page/slide numbers for every claim made.\n"
        "</instruction>\n"
        f"<context_fragments>\n{context_fragments}</context_fragments>\n"
        f"<query>\n{query}\n</query>"
    )

    response = client.generate(model=settings.ollama_lesson_model, prompt=prompt)
    return response["response"]
