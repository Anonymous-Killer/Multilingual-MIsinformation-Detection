from __future__ import annotations

from app.core.config import Settings
from app.orchestrators.base import OrchestratorInterface
from app.orchestrators.mistral import MistralNimOrchestrator, StubOrchestrator


def build_orchestrator(settings: Settings) -> OrchestratorInterface:
    model_name = settings.nim_model.lower()
    if "mistral" in model_name:
        return MistralNimOrchestrator(settings)
    if "glm" in model_name:
        return StubOrchestrator("glm-4.7")
    if "nemotron" in model_name or "llama" in model_name:
        return StubOrchestrator("llama-3.1-nemotron-nano-8b")
    return StubOrchestrator(model_name or "unknown")
