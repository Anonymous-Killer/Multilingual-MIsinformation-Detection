from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

from app.core.config import Settings


LOGGER = logging.getLogger(__name__)


class NimClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def generate_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema_hint: dict[str, Any],
    ) -> dict[str, Any]:
        if not self._settings.nim_api_key:
            raise RuntimeError("NVIDIA NIM API key is not configured.")

        base_payload = {
            "temperature": self._settings.nim_temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"{user_prompt}\n\nReturn only valid JSON matching this shape:\n"
                        f"{json.dumps(schema_hint, ensure_ascii=True)}"
                    ),
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._settings.nim_api_key}",
            "Content-Type": "application/json",
        }
        models_to_try = self._build_model_try_order(model)
        last_error: Optional[Exception] = None

        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            for candidate_model in models_to_try:
                payload = {"model": candidate_model, **base_payload}
                try:
                    response = await client.post(
                        f"{self._settings.nim_base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    if candidate_model != models_to_try[0]:
                        LOGGER.warning(
                            "Primary NIM model unavailable; falling back to %s",
                            candidate_model,
                        )
                    content = response.json()["choices"][0]["message"]["content"]
                    break
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    status_code = exc.response.status_code
                    response_text = exc.response.text[:500]
                    if status_code in {404, 410} and candidate_model != models_to_try[-1]:
                        LOGGER.warning(
                            "NIM model %s returned %s. Trying next fallback. Response: %s",
                            candidate_model,
                            status_code,
                            response_text,
                        )
                        continue

                    LOGGER.error(
                        "NIM request failed for model %s with status %s. Response: %s",
                        candidate_model,
                        status_code,
                        response_text,
                    )
                    raise
            else:  # pragma: no cover
                if last_error is not None:
                    raise last_error
                raise RuntimeError("No NVIDIA NIM models were available to try.")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            LOGGER.error("NIM returned non-JSON content: %s", content)
            raise RuntimeError("NIM returned invalid JSON.") from exc

    def _build_model_try_order(self, requested_model: str) -> list[str]:
        configured_models = self._settings.get_nim_model_candidates()
        candidates = [requested_model]
        candidates.extend(configured_models)

        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = candidate.strip()
            if normalized and normalized not in seen:
                deduped.append(normalized)
                seen.add(normalized)
        return deduped
