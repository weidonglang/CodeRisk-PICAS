from functools import lru_cache
from os import getenv

from pydantic import BaseModel, Field


class Settings(BaseModel):
    analysis_version: str = Field(default="0.1.0")
    config_version: str = Field(default="dev")
    upload_root: str = Field(default="/data/uploads")
    artifact_root: str = Field(default="/data/artifacts")


@lru_cache
def get_settings() -> Settings:
    return Settings(
        analysis_version=getenv("CODERISK_ANALYSIS_VERSION", "0.1.0"),
        config_version=getenv("CODERISK_CONFIG_VERSION", "dev"),
        upload_root=getenv("CODERISK_UPLOAD_DIR", "/data/uploads"),
        artifact_root=getenv("CODERISK_ARTIFACT_DIR", "/data/artifacts"),
    )
