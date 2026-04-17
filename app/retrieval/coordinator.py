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
    """Return meaningful (non-stopword) tokens of length > 2 (used for fast set-overlap filtering)."""
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    return {t for t in tokens if t not in _STOPWORDS}


def _token_weights(text: str) -> dict[str, float]:
    """Return a token → importance-weight mapping for a piece of text.

    The weight reflects how *specific* (i.e. discriminative) each token is:

    • Numbers (e.g. "900", "200") are maximally specific — a casualty count or
      year in a headline must appear in a source that actually covers the same
      event.  Short 1-2 digit numbers ("10", "5") are common and get less
      weight than larger ones.
    • Long alphabetic tokens tend to describe specific concepts ("investigation",
      "parliament") and outweigh short, common ones ("war", "man").
    • Stopwords are excluded entirely.

    This prevents generic context words (country names, short verbs) from
    dominating the similarity score when they match unrelated articles that
    merely mention the same region or topic area.
    """
    weights: dict[str, float] = {}

    # Numeric tokens — higher weight for longer/larger numbers
    for num in re.findall(r"\b\d+\b", text):
        weights[num] = 1.5 if len(num) <= 2 else 3.0

    # Alphabetic content words weighted by character length as a specificity proxy
    for token in re.findall(r"[a-z]{3,}", text.lower()):
        if token in _STOPWORDS:
            continue
        n = len(token)
        if n <= 4:
            w = 0.6   # short words — often common nouns or country codes
        elif n <= 6:
            w = 1.0
        elif n <= 9:
            w = 1.4
        else:
            w = 1.8   # long words are usually domain-specific
        weights[token] = w

    return weights


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
        claim_weights = _token_weights(claim)
        total_claim_weight = max(1.0, sum(claim_weights.values()))

        for item in items:
            doc_weights = _token_weights(
                f"{item.title} {item.snippet} {item.claim_text}"
            )
            # Weighted overlap: sum the importance of each claim token that
            # also appears in the document.  A source that only shares geography
            # keywords ("china", "india") but not the specific event details
            # ("bombed", "900", "injured") will score much lower than one that
            # actually covers the same incident.
            overlap_weight = sum(
                w for token, w in claim_weights.items() if token in doc_weights
            )
            item.similarity_score = min(1.0, overlap_weight / total_claim_weight)
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
