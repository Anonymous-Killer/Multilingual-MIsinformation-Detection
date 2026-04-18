from __future__ import annotations

import os
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

    # ALLOWED_ORIGINS env var: comma-separated list of frontend URLs.
    # Defaults to localhost dev origins so local development keeps working.
    # On Render set it to your Vercel deployment URL, e.g.:
    #   ALLOWED_ORIGINS=https://your-app.vercel.app
    raw = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
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
