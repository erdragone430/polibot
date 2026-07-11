from functools import lru_cache

from FlagEmbedding import FlagReranker

from polibot.config import get_settings


@lru_cache
def get_reranker() -> FlagReranker:
    return FlagReranker(get_settings().reranker_model_name, use_fp16=True)


def rerank(query: str, candidates: list[str], top_n: int = 5) -> list[tuple[int, float]]:
    """(candidate_index, score) pairs for the top_n candidates, best first."""
    if not candidates:
        return []
    reranker = get_reranker()
    pairs = [[query, candidate] for candidate in candidates]
    scores = reranker.compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    return ranked[:top_n]
