import pytest
from typing import Optional

from app.models.schemas import AnalyzeHeadlineRequest, EvidenceSummary, QueryRefinement, RetrievalPlan, RetrievedSource
from app.scoring.engine import DeterministicScoringEngine
from app.services.language import LanguageDetectionService
from app.services.normalization import ClaimNormalizationService
from app.services.pipeline import HeadlineAnalysisPipeline


class FakeOrchestrator:
    async def generate_plan(self, headline: str, language: str) -> RetrievalPlan:
        return RetrievalPlan(
            normalized_claim=headline,
            ambiguity_flags=[],
            search_queries=[headline, f"{headline} fact check"],
            target_languages=[language, "en"],
        )

    async def refine_queries(
        self, headline: str, language: str, initial_results: list[RetrievedSource]
    ) -> QueryRefinement:
        return QueryRefinement(additional_queries=["extra query"], notes=[])

    async def summarize_evidence(
        self, headline: str, language: str, evidence_bundle: list[RetrievedSource]
    ) -> EvidenceSummary:
        return EvidenceSummary(
            evidence_summary="Evidence summary",
            reasoning_trace_summary="Reasoning trace",
            limitations=[],
            uncertainty_flags=[],
        )


class FakeRetrievalCoordinator:
    async def retrieve(
        self,
        claim: str,
        language: str,
        plan: RetrievalPlan,
        refinement: Optional[QueryRefinement] = None,
    ) -> list[RetrievedSource]:
        return [
            RetrievedSource(
                source_id="1",
                source_name="Example Fact Check",
                source_type="fact_check",
                title="Claim reviewed",
                url="https://example.com/fact-check",
                snippet="The article says the claim is false.",
                verdict_label="False",
                agreement="contradicts",
                credibility_weight=0.9,
            )
        ]


@pytest.mark.asyncio
async def test_pipeline_returns_structured_response() -> None:
    pipeline = HeadlineAnalysisPipeline(
        language_service=LanguageDetectionService(),
        normalization_service=ClaimNormalizationService(),
        orchestrator=FakeOrchestrator(),
        retrieval_coordinator=FakeRetrievalCoordinator(),
        scoring_engine=DeterministicScoringEngine(),
    )
    response = await pipeline.analyze(
        AnalyzeHeadlineRequest(headline="Breaking: Viral cure instantly eliminates diabetes")
    )
    assert response.input_headline
    assert response.normalized_claim
    assert response.reliability_score >= 1
    assert response.classification in {
        "true",
        "false",
        "misleading",
        "unverifiable",
        "insufficient_evidence",
    }
    assert response.actual_news_headline == (
        "Not verified: Breaking: Viral cure instantly eliminates diabetes"
    )
    assert response.actual_news_description is not None


class MixedRetrievalCoordinator:
    async def retrieve(
        self,
        claim: str,
        language: str,
        plan: RetrievalPlan,
        refinement: Optional[QueryRefinement] = None,
    ) -> list[RetrievedSource]:
        return [
            RetrievedSource(
                source_id="1",
                source_name="Example Fact Check",
                source_type="fact_check",
                title="Viral cure instantly eliminates diabetes",
                url="https://example.com/fact-check",
                snippet="A fact-check article says the claim is false.",
                verdict_label="False",
                agreement="contradicts",
                similarity_score=0.95,
                credibility_weight=0.95,
            ),
            RetrievedSource(
                source_id="2",
                source_name="Reuters",
                source_type="web_search",
                title="Doctors warn viral diabetes cure posts are false",
                url="https://example.com/news",
                snippet="Doctors say no instant diabetes cure exists and the viral claim is false.",
                agreement="related",
                similarity_score=0.92,
                credibility_weight=0.9,
            ),
        ]


@pytest.mark.asyncio
async def test_pipeline_prefers_non_fact_check_headline_when_available() -> None:
    pipeline = HeadlineAnalysisPipeline(
        language_service=LanguageDetectionService(),
        normalization_service=ClaimNormalizationService(),
        orchestrator=FakeOrchestrator(),
        retrieval_coordinator=MixedRetrievalCoordinator(),
        scoring_engine=DeterministicScoringEngine(),
    )
    response = await pipeline.analyze(
        AnalyzeHeadlineRequest(headline="Breaking: Viral cure instantly eliminates diabetes")
    )
    assert response.actual_news_headline == "Doctors warn viral diabetes cure posts are false"
    assert response.actual_news_description is not None
