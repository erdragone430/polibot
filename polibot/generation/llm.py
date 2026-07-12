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

    numbered_sources = "\n\n".join(
        f"[{i}] (course: {s['metadata'].get('course')}, topic: {s['metadata'].get('topic')}, "
        f"slide: {s['metadata'].get('slide')})\n{s['text']}"
        for i, s in enumerate(sources, start=1)
    )
    prompt = f"{ANSWER_SYSTEM_PROMPT}\n\nSources:\n{numbered_sources}\n\nQuestion: {query}"

    response = client.generate(model=settings.ollama_lesson_model, prompt=prompt)
    return response["response"]
