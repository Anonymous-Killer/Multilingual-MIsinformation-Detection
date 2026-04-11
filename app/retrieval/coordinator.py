from __future__ import annotations

from collections import OrderedDict
from typing import Optional

from app.adapters.fact_check import GoogleFactCheckAdapter
from app.adapters.web_search import TavilySearchAdapter
from app.models.schemas import QueryRefinement, RetrievedSource, RetrievalPlan
from app.vectorstore.chroma_store import ChromaVectorStore
from app.vectorstore.embeddings import HashingEmbeddingProvider


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

        combined = self._deduplicate(fact_checks + vector_hits + web_results)
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
        lowered_claim = claim.lower()
        for item in items:
            haystack = f"{item.title} {item.snippet} {item.claim_text}".lower()
            token_overlap = len(set(lowered_claim.split()) & set(haystack.split()))
            item.similarity_score = min(1.0, token_overlap / max(1, len(set(lowered_claim.split()))))
            item.agreement = RetrievalCoordinator._infer_agreement(lowered_claim, item)
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
