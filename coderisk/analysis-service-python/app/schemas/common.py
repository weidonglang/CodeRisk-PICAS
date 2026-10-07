from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class AnalysisEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    error_code: str | None = Field(default=None, alias="errorCode")
    message: str
    analysis_version: str = Field(alias="analysisVersion")
    config_version: str = Field(alias="configVersion")
    result: T | None

    @classmethod
    def success_response(
        cls,
        result: T,
        analysis_version: str,
        config_version: str,
    ) -> "AnalysisEnvelope[T]":
        return cls(
            success=True,
            errorCode=None,
            message="success",
            analysisVersion=analysis_version,
            configVersion=config_version,
            result=result,
        )


class HealthResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    service: str
    analysis_version: str = Field(alias="analysisVersion")
    checked_at: datetime = Field(alias="checkedAt")
    upload_root: str = Field(alias="uploadRoot")
    artifact_root: str = Field(alias="artifactRoot")
