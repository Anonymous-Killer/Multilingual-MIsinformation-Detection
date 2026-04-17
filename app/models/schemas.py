from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


ClassificationLabel = Literal[
    "true",
    "false",
    "misleading",
    "unverifiable",
    "insufficient_evidence",
]


class AnalyzeHeadlineRequest(BaseModel):
    headline: str = Field(min_length=5, max_length=500)


class RetrievedSource(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    title: str
    url: Optional[HttpUrl] = None
    language: str = "unknown"
    snippet: str = ""
    claim_text: str = ""
    verdict_label: Optional[str] = None
    published_at: Optional[datetime] = None
    credibility_weight: float = 0.5
    similarity_score: float = 0.0
    agreement: str = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalPlan(BaseModel):
    normalized_claim: str
    ambiguity_flags: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    target_languages: list[str] = Field(default_factory=list)


class QueryRefinement(BaseModel):
    additional_queries: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class EvidenceSummary(BaseModel):
    evidence_summary: str
    reasoning_trace_summary: str
    limitations: list[str] = Field(default_factory=list)
    uncertainty_flags: list[str] = Field(default_factory=list)


class EvidenceFeatures(BaseModel):
    fact_check_match_score: float = 0.0
    support_score: float = 0.0
    contradiction_score: float = 0.0
    source_credibility_score: float = 0.0
    recency_score: float = 0.0
    coverage_score: float = 0.0
    uncertainty_penalty: float = 0.0


class AnalyzeHeadlineResponse(BaseModel):
    input_headline: str
    detected_language: str
    normalized_claim: str
    classification: ClassificationLabel
    retrieved_sources: list[RetrievedSource]
    evidence_summary: str
    reliability_score: int = Field(ge=1, le=10)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_trace_summary: str
    limitations: list[str]
    uncertainty_flags: list[str]
    evidence_features: EvidenceFeatures
    actual_news_headline: Optional[str] = None
    actual_news_description: Optional[str] = None
