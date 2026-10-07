from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas.common import AnalysisEnvelope, HealthResult

router = APIRouter(prefix="/internal", tags=["health"])


@router.get("/health", response_model=AnalysisEnvelope[HealthResult])
def health(settings: Settings = Depends(get_settings)) -> AnalysisEnvelope[HealthResult]:
    result = HealthResult(
        status="UP",
        service="coderisk-analysis-service",
        analysis_version=settings.analysis_version,
        checked_at=datetime.now(timezone.utc),
        upload_root=settings.upload_root,
        artifact_root=settings.artifact_root,
    )
    return AnalysisEnvelope.success_response(
        result=result,
        analysis_version=settings.analysis_version,
        config_version=settings.config_version,
    )
