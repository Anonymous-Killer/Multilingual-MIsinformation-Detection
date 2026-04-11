from __future__ import annotations

import json
import logging
from typing import Any

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

        payload = {
            "model": model,
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
        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{self._settings.nim_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            LOGGER.error("NIM returned non-JSON content: %s", content)
            raise RuntimeError("NIM returned invalid JSON.") from exc
