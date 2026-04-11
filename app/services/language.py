from __future__ import annotations

from langdetect import DetectorFactory, LangDetectException, detect


DetectorFactory.seed = 0


class LanguageDetectionService:
    async def detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"
