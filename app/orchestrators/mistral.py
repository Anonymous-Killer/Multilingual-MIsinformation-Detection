from __future__ import annotations

from collections import Counter

from app.core.config import Settings
from app.models.schemas import EvidenceSummary, QueryRefinement, RetrievalPlan, RetrievedSource
from app.orchestrators.base import OrchestratorInterface
from app.orchestrators.nim import NimClient


class MistralNimOrchestrator(OrchestratorInterface):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = NimClient(settings)

    async def generate_plan(self, headline: str, language: str) -> RetrievalPlan:
        schema_hint = {
            "normalized_claim": "short normalized claim",
            "ambiguity_flags": ["entity ambiguity"],
            "search_queries": ["claim query", "fact check query"],
            "target_languages": [language, "en"],
        }
        data = await self._client.generate_json(
            model=self._settings.nim_model,
            system_prompt=(
                "You are a retrieval planner for misinformation detection. "
                "Normalize the headline into a claim, identify ambiguity, and propose search queries. "
                "Never infer truth. Optimize for fact-check retrieval first."
            ),
            user_prompt=f"Headline: {headline}\nDetected language: {language}",
            schema_hint=schema_hint,
        )
        return RetrievalPlan.model_validate(data)

    async def refine_queries(
        self, headline: str, language: str, initial_results: list[RetrievedSource]
    ) -> QueryRefinement:
        summary = [
            {
                "title": item.title,
                "source_name": item.source_name,
                "verdict_label": item.verdict_label,
                "snippet": item.snippet[:300],
            }
            for item in initial_results[:6]
        ]
        data = await self._client.generate_json(
            model=self._settings.nim_model,
            system_prompt=(
                "You refine retrieval queries for evidence gathering. "
                "Use the current evidence to find missing angles, but do not evaluate truth."
            ),
            user_prompt=(
                f"Headline: {headline}\nDetected language: {language}\nCurrent results: {summary}"
            ),
            schema_hint={
                "additional_queries": ["alternative wording of the claim"],
                "notes": ["missing actor and date context"],
            },
        )
        return QueryRefinement.model_validate(data)

    async def summarize_evidence(
        self, headline: str, language: str, evidence_bundle: list[RetrievedSource]
    ) -> EvidenceSummary:
        evidence = [
            {
                "source_id": source.source_id,
                "title": source.title,
                "source_name": source.source_name,
                "agreement": source.agreement,
                "verdict_label": source.verdict_label,
                "credibility_weight": source.credibility_weight,
                "snippet": source.snippet[:400],
            }
            for source in evidence_bundle[:10]
        ]
        data = await self._client.generate_json(
            model=self._settings.nim_model,
            system_prompt=(
                "You summarize retrieved evidence for a misinformation detection backend. "
                "Ground every statement in the provided evidence. "
                "Do not state that the claim is true or false unless the evidence itself says so. "
                "Mention uncertainty explicitly."
            ),
            user_prompt=f"Headline: {headline}\nLanguage: {language}\nEvidence: {evidence}",
            schema_hint={
                "evidence_summary": "brief summary of the retrieved evidence",
                "reasoning_trace_summary": "short explanation of how evidence was compared",
                "limitations": ["limited corroboration"],
                "uncertainty_flags": ["conflicting evidence"],
            },
        )
        return EvidenceSummary.model_validate(data)


class StubOrchestrator(OrchestratorInterface):
    def __init__(self, model_name: str):
        self.model_name = model_name

    async def generate_plan(self, headline: str, language: str) -> RetrievalPlan:
        queries = [headline, f"{headline} fact check", f"{headline} verification"]
        return RetrievalPlan(
            normalized_claim=headline.strip(),
            ambiguity_flags=[],
            search_queries=queries,
            target_languages=[language, "en"] if language != "en" else ["en"],
        )

    async def refine_queries(
        self, headline: str, language: str, initial_results: list[RetrievedSource]
    ) -> QueryRefinement:
        seen_sources = Counter(item.source_name for item in initial_results)
        notes = [f"stub:{self.model_name} saw {len(initial_results)} results"]
        if seen_sources:
            notes.append(f"top_source:{seen_sources.most_common(1)[0][0]}")
        return QueryRefinement(
            additional_queries=[f"{headline} latest evidence", f"{headline} source documents"],
            notes=notes,
        )

    async def summarize_evidence(
        self, headline: str, language: str, evidence_bundle: list[RetrievedSource]
    ) -> EvidenceSummary:
        titles = ", ".join(source.title for source in evidence_bundle[:3]) or "No evidence found"
        limitations = [] if evidence_bundle else ["No external evidence retrieved."]
        return EvidenceSummary(
            evidence_summary=f"Evidence reviewed for '{headline}': {titles}.",
            reasoning_trace_summary=(
                "The backend compared retrieved fact-check and web sources, then deferred final "
                "scoring to deterministic evidence features."
            ),
            limitations=limitations,
            uncertainty_flags=[] if evidence_bundle else ["insufficient_evidence"],
        )
