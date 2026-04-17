from __future__ import annotations

import re
from collections import OrderedDict
from typing import Optional

from app.adapters.fact_check import GoogleFactCheckAdapter
from app.adapters.web_search import TavilySearchAdapter
from app.models.schemas import QueryRefinement, RetrievedSource, RetrievalPlan
from app.vectorstore.chroma_store import ChromaVectorStore
from app.vectorstore.embeddings import HashingEmbeddingProvider

# Common words that appear in almost every sentence and cause false overlaps
# when filtering vector store hits by token intersection.
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "about",
    "and", "or", "but", "not", "that", "this", "it", "its", "which",
    "who", "what", "how", "when", "where", "there", "their", "they",
    "he", "she", "we", "you", "i", "me", "him", "her", "us", "them",
    "s", "t", "re", "ve", "ll", "d",
})


def _content_tokens(text: str) -> set[str]:
    """Return meaningful (non-stopword) tokens of length > 2."""
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    return {t for t in tokens if t not in _STOPWORDS}


class RetrievalCoordinator:
    def __init__(
        self,
        fact_check_adapter: GoogleFactCheckAdapter,
        search_adapter: TavilySearchAdapter,
        embedding_provider: HashingEmbeddingProvider,
        vector_store: ChromaVectorStore,
    ):
        self._fact_check_adapter = fact_check_adapter
        self._search_adapter = search_adapter
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    async def retrieve(
        self,
        claim: str,
        language: str,
        plan: RetrievalPlan,
        refinement: Optional[QueryRefinement] = None,
    ) -> list[RetrievedSource]:
        queries = list(plan.search_queries)
        if refinement:
            queries.extend(refinement.additional_queries)

        fact_checks = await self._fact_check_adapter.search_claims(claim, language, queries)
        query_embedding = (await self._embedding_provider.embed_texts([claim]))[0]
        vector_hits = await self._vector_store.search(query_embedding=query_embedding, k=5)

        web_results: list[RetrievedSource] = []
        for query in queries[:3]:
            web_results.extend(await self._search_adapter.search(query, language, limit=3))

        # The vector store persists across all requests. Filter its hits using
        # *content-word* overlap (stopwords excluded) so that documents from
        # previous unrelated queries are not included.  Fact-check and web
        # results are always kept because they are fetched fresh per request.
        claim_content = _content_tokens(claim)
        relevant_vector_hits = [
            h for h in vector_hits
            if claim_content & _content_tokens(self._document_text(h))
        ]

        combined = self._deduplicate(fact_checks + relevant_vector_hits + web_results)
        embeddings = await self._embedding_provider.embed_texts(
            [self._document_text(item) for item in combined]
        )
        await self._vector_store.upsert(combined, embeddings)
        ranked = self._rank(claim, combined)
        return ranked[:10]

    @staticmethod
    def _deduplicate(items: list[RetrievedSource]) -> list[RetrievedSource]:
        deduped: OrderedDict[str, RetrievedSource] = OrderedDict()
        for item in items:
            key = str(item.url or item.title).lower().strip()
            if key not in deduped:
                deduped[key] = item
        return list(deduped.values())

    @staticmethod
    def _document_text(item: RetrievedSource) -> str:
        return " ".join(filter(None, [item.title, item.snippet, item.claim_text]))

    @staticmethod
    def _rank(claim: str, items: list[RetrievedSource]) -> list[RetrievedSource]:
        claim_content = _content_tokens(claim)
        for item in items:
            doc_content = _content_tokens(
                f"{item.title} {item.snippet} {item.claim_text}"
            )
            overlap = len(claim_content & doc_content)
            item.similarity_score = min(1.0, overlap / max(1, len(claim_content)))
            item.agreement = RetrievalCoordinator._infer_agreement(claim.lower(), item)
        return sorted(
            items,
            key=lambda item: (
                item.source_type != "fact_check",
                -(item.similarity_score + item.credibility_weight),
            ),
        )

    @staticmethod
    def _infer_agreement(claim: str, item: RetrievedSource) -> str:
        verdict = (item.verdict_label or "").lower()
        text = f"{item.title} {item.snippet}".lower()
        if any(token in verdict for token in ("false", "incorrect", "pants on fire")):
            return "contradicts"
        if any(token in verdict for token in ("true", "correct")):
            return "supports"
        if any(token in text for token in claim.split()[:4]):
            return "related"
        return "unknown"
