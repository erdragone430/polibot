from unittest.mock import MagicMock, patch

from polibot.ingestion.chunking import Page, chunk_pages
from polibot.ingestion.embedding import embed_texts


def test_chunk_pages_tags_each_chunk_with_its_own_page():
    pages = [
        Page(number=1, text="Intro to loops. " * 5),
        Page(number=2, text="Recursion basics. " * 5),
    ]
    nodes = chunk_pages(pages, course="CS101", topic="algorithms", chunk_size=20, chunk_overlap=5)
    assert nodes
    assert {node.metadata["page"] for node in nodes} == {1, 2}


def test_embed_texts_combines_ollama_dense_and_fastembed_sparse():
    fake_ollama_client = MagicMock()
    fake_ollama_client.embed.return_value = {"embeddings": [[0.1, 0.2]]}

    fake_sparse = MagicMock(indices=MagicMock(tolist=lambda: [5, 12]), values=MagicMock(tolist=lambda: [0.9, 0.4]))
    fake_sparse_model = MagicMock()
    fake_sparse_model.embed.return_value = [fake_sparse]

    with (
        patch("polibot.ingestion.embedding.ollama.Client", return_value=fake_ollama_client),
        patch("polibot.ingestion.embedding.get_sparse_model", return_value=fake_sparse_model),
    ):
        results = embed_texts(["hello world"])

    assert results[0]["dense"] == [0.1, 0.2]
    assert set(results[0]["sparse"].indices) == {5, 12}


if __name__ == "__main__":
    test_chunk_pages_tags_each_chunk_with_its_own_page()
    test_embed_texts_combines_ollama_dense_and_fastembed_sparse()
    print("ok")
