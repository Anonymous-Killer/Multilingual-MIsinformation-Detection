from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.schemas import EvidenceSummary, QueryRefinement, RetrievalPlan, RetrievedSource


class OrchestratorInterface(ABC):
    @abstractmethod
    async def generate_plan(self, headline: str, language: str) -> RetrievalPlan:
        raise NotImplementedError

    @abstractmethod
    async def refine_queries(
        self, headline: str, language: str, initial_results: list[RetrievedSource]
    ) -> QueryRefinement:
        raise NotImplementedError

    @abstractmethod
    async def summarize_evidence(
        self, headline: str, language: str, evidence_bundle: list[RetrievedSource]
    ) -> EvidenceSummary:
        raise NotImplementedError
