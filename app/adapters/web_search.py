from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Optional

import httpx

from app.core.config import Settings
from app.models.schemas import RetrievedSource


class TavilySearchAdapter:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def search(self, query: str, language: str, limit: int = 5) -> list[RetrievedSource]:
        if not self._settings.tavily_api_key:
            return []

        payload = {
            "api_key": self._settings.tavily_api_key,
            "query": query,
            "max_results": limit,
            "include_answer": False,
            "include_raw_content": False,
            "search_depth": "advanced",
            "topic": "news",
        }
        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            response = await client.post(self._settings.tavily_base_url, json=payload)
            response.raise_for_status()
            data = response.json()
        return self._normalize(data.get("results", []), language)

    def _normalize(self, results: list[dict[str, Any]], language: str) -> list[RetrievedSource]:
        sources: list[RetrievedSource] = []
        for index, result in enumerate(results):
            stable_id = self._build_source_id(result, index)
            sources.append(
                RetrievedSource(
                    source_id=stable_id,
                    source_name=result.get("source", "Web Search"),
                    source_type="web_search",
                    title=result.get("title", "Search result"),
                    url=result.get("url"),
                    language=language,
                    snippet=result.get("content", ""),
                    claim_text=result.get("title", ""),
                    published_at=self._parse_datetime(result.get("published_date")),
                    credibility_weight=self._credibility_from_domain(result.get("url", "")),
                    metadata={"raw_result": result},
                )
            )
        return sources

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _credibility_from_domain(url: str) -> float:
        high_confidence_signals = ("reuters.com", "apnews.com", "bbc.com", "factcheck.org")
        medium_confidence_signals = ("wikipedia.org", "nytimes.com", "theguardian.com")
        if any(signal in url for signal in high_confidence_signals):
            return 0.85
        if any(signal in url for signal in medium_confidence_signals):
            return 0.7
        return 0.55

    @staticmethod
    def _build_source_id(result: dict[str, Any], index: int) -> str:
        raw_value = result.get("url") or result.get("title") or f"result-{index}"
        digest = hashlib.sha1(raw_value.encode("utf-8")).hexdigest()[:12]
        return f"tavily-{digest}"
