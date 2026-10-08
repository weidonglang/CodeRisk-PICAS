from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.analyzers.token_similarity import analyze_token_pair
from app.core.path_guard import ensure_path_under_root
from app.schemas.analyze_schema import AnalyzeMockRequest, AnalyzeMockResult
from app.schemas.common import AnalysisEnvelope

router = APIRouter(prefix="/internal/analyze", tags=["analyze"])


def _validate_submission_paths(request: AnalyzeMockRequest, settings: Settings) -> None:
    for submission in (request.submission_a, request.submission_b):
        if submission.raw_code_path:
            if not ensure_path_under_root(submission.raw_code_path, settings.upload_root):
                raise HTTPException(
                    status_code=400,
                    detail=f"rawCodePath must stay under upload root: {settings.upload_root}",
                )


@router.post("/pair", response_model=AnalysisEnvelope[AnalyzeMockResult])
def analyze_pair(
    request: AnalyzeMockRequest,
    settings: Settings = Depends(get_settings),
) -> AnalysisEnvelope[AnalyzeMockResult]:
    _validate_submission_paths(request, settings)
    try:
        result = analyze_token_pair(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AnalysisEnvelope.success_response(
        result=result,
        analysis_version=settings.analysis_version,
        config_version=settings.config_version,
    )


@router.post("/mock", response_model=AnalysisEnvelope[AnalyzeMockResult])
def analyze_mock(
    request: AnalyzeMockRequest,
    settings: Settings = Depends(get_settings),
) -> AnalysisEnvelope[AnalyzeMockResult]:
    _validate_submission_paths(request, settings)

    result = AnalyzeMockResult(
        task_id=request.task_id,
        submission_a_id=request.submission_a.id,
        submission_b_id=request.submission_b.id,
    )
    return AnalysisEnvelope.success_response(
        result=result,
        analysis_version=settings.analysis_version,
        config_version=settings.config_version,
    )
