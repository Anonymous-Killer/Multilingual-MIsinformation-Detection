from __future__ import annotations

import logging
import re
from typing import Optional

from app.models.schemas import (
    AnalyzeHeadlineRequest,
    AnalyzeHeadlineResponse,
    EvidenceSummary,
    RetrievedSource,
)
from app.orchestrators.base import OrchestratorInterface
from app.retrieval.coordinator import RetrievalCoordinator
from app.scoring.engine import DeterministicScoringEngine
from app.services.language import LanguageDetectionService
from app.services.normalization import ClaimNormalizationService


LOGGER = logging.getLogger(__name__)


class HeadlineAnalysisPipeline:
    _WORD_PATTERN = re.compile(r"\S+")

    def __init__(
        self,
        language_service: LanguageDetectionService,
        normalization_service: ClaimNormalizationService,
        orchestrator: OrchestratorInterface,
        retrieval_coordinator: RetrievalCoordinator,
        scoring_engine: DeterministicScoringEngine,
    ):
        self._language_service = language_service
        self._normalization_service = normalization_service
        self._orchestrator = orchestrator
        self._retrieval_coordinator = retrieval_coordinator
        self._scoring_engine = scoring_engine

    async def analyze(self, request: AnalyzeHeadlineRequest) -> AnalyzeHeadlineResponse:
        detected_language = await self._language_service.detect_language(request.headline)
        normalized_claim = await self._normalization_service.normalize(request.headline)

        plan = await self._orchestrator.generate_plan(normalized_claim, detected_language)
        normalized_claim = plan.normalized_claim or normalized_claim

        initial_results = await self._retrieval_coordinator.retrieve(
            normalized_claim,
            detected_language,
            plan,
        )
        refinement = None
        if len(initial_results) < 3:
            refinement = await self._orchestrator.refine_queries(
                normalized_claim,
                detected_language,
                initial_results,
            )
        retrieved_sources = await self._retrieval_coordinator.retrieve(
            normalized_claim,
            detected_language,
            plan,
            refinement,
        )
        classification, reliability_score, confidence, evidence_features = (
            self._scoring_engine.score(retrieved_sources)
        )
        try:
            summary = await self._orchestrator.summarize_evidence(
                normalized_claim,
                detected_language,
                retrieved_sources,
            )
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Falling back to local summary generation: %s", exc)
            summary = EvidenceSummary(
                evidence_summary="Summary unavailable from orchestrator. Review retrieved sources directly.",
                reasoning_trace_summary=(
                    "The backend gathered fact-check and search evidence, then scored the claim "
                    "with deterministic features."
                ),
                limitations=["Orchestrator summary unavailable."],
                uncertainty_flags=["summary_unavailable"],
            )

        if plan.ambiguity_flags:
            summary.uncertainty_flags.extend(
                flag for flag in plan.ambiguity_flags if flag not in summary.uncertainty_flags
            )

        actual_news_headline = None
        actual_news_description = None
        if reliability_score <= 7:
            actual_news_headline, actual_news_description = self._build_low_score_clarification(
                retrieved_sources,
                summary,
            )

        return AnalyzeHeadlineResponse(
            input_headline=request.headline,
            detected_language=detected_language,
            normalized_claim=normalized_claim,
            classification=classification,
            retrieved_sources=retrieved_sources,
            evidence_summary=summary.evidence_summary,
            reliability_score=reliability_score,
            confidence=confidence,
            reasoning_trace_summary=summary.reasoning_trace_summary,
            limitations=summary.limitations,
            uncertainty_flags=summary.uncertainty_flags,
            evidence_features=evidence_features,
            actual_news_headline=actual_news_headline,
            actual_news_description=actual_news_description,
        )

    def _build_low_score_clarification(
        self,
        retrieved_sources: list[RetrievedSource],
        summary: EvidenceSummary,
    ) -> tuple[Optional[str], Optional[str]]:
        primary_source = self._select_primary_source(retrieved_sources)
        headline = primary_source.title if primary_source else None

        description_candidates = []
        if primary_source:
            description_candidates.extend(
                [
                    primary_source.snippet,
                    primary_source.claim_text,
                    f"{primary_source.source_name}: {primary_source.title}",
                ]
            )
        description_candidates.append(summary.evidence_summary)

        description = None
        for candidate in description_candidates:
            description = self._normalize_description(candidate)
            if description:
                break

        return headline, description

    def _select_primary_source(
        self,
        retrieved_sources: list[RetrievedSource],
    ) -> Optional[RetrievedSource]:
        if not retrieved_sources:
            return None

        ranked = sorted(
            retrieved_sources,
            key=lambda source: (
                source.source_type == "fact_check",
                -(source.similarity_score + source.credibility_weight),
            ),
        )
        return ranked[0]

    def _normalize_description(self, text: str) -> Optional[str]:
        cleaned = " ".join(text.split()).strip()
        if not cleaned:
            return None

        words = self._WORD_PATTERN.findall(cleaned)
        if not words:
            return None

        if len(words) < 30:
            cleaned = (
                f"{cleaned} This summary reflects the most relevant retrieved reporting and "
                "fact-check evidence available to the backend at analysis time."
            )
            words = self._WORD_PATTERN.findall(cleaned)

        limited_words = words[:50]
        if len(limited_words) >= 30:
            return " ".join(limited_words)
        return cleaned
