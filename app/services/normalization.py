from __future__ import annotations

import re


class ClaimNormalizationService:
    _TRAILING_PUNCTUATION = re.compile(r"[!?]+$")
    _MULTISPACE = re.compile(r"\s+")

    async def normalize(self, headline: str) -> str:
        text = headline.strip()
        text = self._TRAILING_PUNCTUATION.sub("", text)
        text = self._MULTISPACE.sub(" ", text)
        return text
