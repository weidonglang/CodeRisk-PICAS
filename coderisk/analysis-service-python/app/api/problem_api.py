from fastapi import APIRouter, Depends

from app.analyzers.problem_profile import build_problem_profile, calculate_dynamic_threshold
from app.config import Settings, get_settings
from app.schemas.analyze_schema import ProblemScoreRequest, ProblemScoreResult
from app.schemas.common import AnalysisEnvelope

router = APIRouter(prefix="/internal/problem", tags=["problem-profile"])


@router.post("/score", response_model=AnalysisEnvelope[ProblemScoreResult])
def score_problem(
    request: ProblemScoreRequest,
    settings: Settings = Depends(get_settings),
) -> AnalysisEnvelope[ProblemScoreResult]:
    profile = build_problem_profile(request.question, request.config)
    threshold = calculate_dynamic_threshold(profile, request.config)
    return AnalysisEnvelope.success_response(
        result=ProblemScoreResult(
            questionId=request.question.id,
            problemProfile=profile.as_dict(),
            thresholdAdjustment=threshold.as_dict(),
        ),
        analysis_version=settings.analysis_version,
        config_version=settings.config_version,
    )
