from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.fact_check import GoogleFactCheckAdapter
from app.adapters.web_search import TavilySearchAdapter
from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.orchestrators.factory import build_orchestrator
from app.retrieval.coordinator import RetrievalCoordinator
from app.scoring.engine import DeterministicScoringEngine
from app.services.language import LanguageDetectionService
from app.services.normalization import ClaimNormalizationService
from app.services.pipeline import HeadlineAnalysisPipeline
from app.vectorstore.chroma_store import ChromaVectorStore
from app.vectorstore.embeddings import HashingEmbeddingProvider


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    application = FastAPI(title=settings.app_name)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    application.include_router(router, prefix=settings.api_prefix)
    return application


@lru_cache(maxsize=1)
def get_pipeline() -> HeadlineAnalysisPipeline:
    settings: Settings = get_settings()
    return HeadlineAnalysisPipeline(
        language_service=LanguageDetectionService(),
        normalization_service=ClaimNormalizationService(),
        orchestrator=build_orchestrator(settings),
        retrieval_coordinator=RetrievalCoordinator(
            fact_check_adapter=GoogleFactCheckAdapter(settings),
            search_adapter=TavilySearchAdapter(settings),
            embedding_provider=HashingEmbeddingProvider(),
            vector_store=ChromaVectorStore(settings),
        ),
        scoring_engine=DeterministicScoringEngine(),
    )


app = create_app()
