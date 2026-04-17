from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(r"C:\Codes\Projects\Multilingual Misinformation Detection Agent")


class Settings(BaseSettings):
    app_name: str = "Multilingual Misinformation Detection Agent"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    request_timeout_seconds: int = 30

    nim_base_url: str = Field(default="https://integrate.api.nvidia.com/v1")
    nim_api_key: str = Field(default="")
    nim_model: str = Field(default="mistralai/mistral-small-3.1-24b-instruct-2503")
    nim_fallback_models: str = Field(default="")
    nim_temperature: float = Field(default=0.1)

    google_fact_check_api_key: str = Field(default="")
    google_fact_check_base_url: str = Field(
        default="https://factchecktools.googleapis.com/v1alpha1/claims:search"
    )

    tavily_api_key: str = Field(default="")
    tavily_base_url: str = Field(default="https://api.tavily.com/search")

    chroma_path: Path = Field(default=PROJECT_ROOT / "data" / "chroma")
    chroma_collection_name: str = Field(default="misinformation_evidence")
    embedding_provider: str = Field(default="hashing")
    allow_mock_external_services: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_nim_model_candidates(self) -> list[str]:
        candidates = [self.nim_model]
        if self.nim_fallback_models:
            candidates.extend(
                item.strip()
                for item in self.nim_fallback_models.split(",")
                if item.strip()
            )

        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = candidate.strip()
            if normalized and normalized not in seen:
                deduped.append(normalized)
                seen.add(normalized)
        return deduped


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    return settings

