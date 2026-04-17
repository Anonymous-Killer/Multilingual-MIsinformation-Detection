from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Optional

import httpx

from app.core.config import Settings
from app.models.schemas import RetrievedSource


class GoogleFactCheckAdapter:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def search_claims(
        self, claim: str, language: str, queries: list[str]
    ) -> list[RetrievedSource]:
        if not self._settings.google_fact_check_api_key:
            return []

        params = {
            "key": self._settings.google_fact_check_api_key,
            "query": queries[0] if queries else claim,
            "languageCode": language if language != "unknown" else None,
            "pageSize": 5,
        }
        params = {key: value for key, value in params.items() if value}
        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            response = await client.get(self._settings.google_fact_check_base_url, params=params)
            response.raise_for_status()
            payload = response.json()
        return self._normalize_claims(payload.get("claims", []), language)

    def _normalize_claims(
        self,
        claims: list[dict[str, Any]],
        language: str,
    ) -> list[RetrievedSource]:
        normalized: list[RetrievedSource] = []
        for index, claim in enumerate(claims):
            reviews = claim.get("claimReview", [])
            review = reviews[0] if reviews else {}
            published_at = review.get("reviewDate")
            stable_id = self._build_source_id(claim, review, index)
            normalized.append(
                RetrievedSource(
                    source_id=stable_id,
                    source_name=review.get("publisher", {}).get("name", "Google Fact Check"),
                    source_type="fact_check",
                    title=review.get("title") or claim.get("text", "Fact check result"),
                    url=review.get("url"),
                    language=language if language != "unknown" else "unknown",
                    snippet=claim.get("text", ""),
                    claim_text=claim.get("text", ""),
                    verdict_label=review.get("textualRating"),
                    published_at=self._parse_datetime(published_at),
                    credibility_weight=0.95,
                    metadata={"raw_claim": claim},
                )
            )
        return normalized

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _build_source_id(
        claim: dict[str, Any],
        review: dict[str, Any],
        index: int,
    ) -> str:
        raw_value = (
            review.get("url")
            or review.get("title")
            or claim.get("text")
            or f"claim-{index}"
        )
        digest = hashlib.sha1(raw_value.encode("utf-8")).hexdigest()[:12]
        return f"google-fact-check-{digest}"
