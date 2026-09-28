import re

from app.models import Chunk, RetrievalResult


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


class Retriever:

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks

    def search(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[RetrievalResult]:

        query_words = tokenize(query)

        if not query_words:
            return []

        results = []

        for chunk in self.chunks:

            chunk_words = tokenize(chunk.content)

            matches = query_words.intersection(
                chunk_words
            )

            score = len(matches) / len(query_words)

            if score > min_score:

                results.append(
                    RetrievalResult(
                        chunk=chunk,
                        score=score,
                    )
                )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:top_k]