from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import AnalyzeHeadlineRequest, AnalyzeHeadlineResponse
from app.services.pipeline import HeadlineAnalysisPipeline


router = APIRouter()


def get_pipeline_dependency() -> HeadlineAnalysisPipeline:
    from app.main import get_pipeline

    return get_pipeline()


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze-headline", response_model=AnalyzeHeadlineResponse)
async def analyze_headline(
    request: AnalyzeHeadlineRequest,
    pipeline: HeadlineAnalysisPipeline = Depends(get_pipeline_dependency),
) -> AnalyzeHeadlineResponse:
    return await pipeline.analyze(request)
