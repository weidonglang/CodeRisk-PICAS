"""Typed process metadata, not an AI-attribution or misconduct classifier."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path, PureWindowsPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, field_validator

Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
Sha = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Relation = Literal["HUMAN_INDEPENDENT", "AI_INDEPENDENT_SAME_MODEL", "AI_INDEPENDENT_CROSS_MODEL",
                   "KNOWN_DERIVED_HUMAN", "KNOWN_DERIVED_AI_REWRITE", "UNCERTAIN"]
Split = Literal["validation", "test"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Question(Record):
    problem_id: Identifier
    problem_family: Identifier
    language: Literal["python", "java"]
    title: Text
    question_path: str
    question_text_sha256: Sha
    difficulty_proxy: Literal["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
    solution_space_proxy: Literal["NARROW", "BROAD", "UNKNOWN"]
    template_id: Identifier | None
    template_path: str | None
    hidden_test_policy: Text
    course_ai_policy: Literal["ALLOWED", "PROHIBITED", "UNKNOWN"]
    confidentiality: Literal["PUBLIC", "LOCAL_RESTRICTED", "SYNTHETIC"]
    license_or_authorization_ref: str
    split: Split


class GenerationSession(Record):
    generation_session_id: Identifier
    problem_id: Identifier
    source_family_id: Identifier
    session_independence_basis: Text
    provider: Identifier
    model_id: Identifier
    model_version_or_snapshot: Text
    access_mode: Literal["MANUAL_EXPORT", "AUTHORIZED_API_EXPORT", "SYNTHETIC_FIXTURE"]
    generation_time_utc: str
    prompt_id: Identifier
    prompt_family: Identifier
    prompt_sha256: Sha
    full_prompt_storage_ref: str
    session_record_ref: str
    temperature: float | None
    top_p: float | None
    seed_if_supported: int | None
    settings_semantics: Text
    revision_count: int = Field(ge=0)
    human_edits: bool
    shared_upstream_refs: list[str]
    synthetic: bool
    attempt_status: Literal["COMPLETED", "FAILED", "TRUNCATED", "UNKNOWN"] = "UNKNOWN"
    error_or_truncation_ref: str | None = None

    @field_validator("generation_time_utc")
    @classmethod
    def utc(cls, value):
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timestamp.utcoffset() != timedelta(0):
            raise ValueError("Explicit UTC required")
        return value

    @field_validator("temperature", "top_p")
    @classmethod
    def finite_parameter(cls, value):
        import math
        if value is not None and not math.isfinite(value):
            raise ValueError("Finite parameter or explicit null required")
        return value


class Artifact(Record):
    sample_id: Identifier
    problem_id: Identifier
    source_family_id: Identifier
    generation_session_id: Identifier | None
    origin_type: Literal["HUMAN", "AI", "UNKNOWN"]
    ai_assistance_type: Literal["HUMAN_ONLY", "PURE_AI", "AI_ASSISTED", "UNKNOWN"]
    parent_sample_id: Identifier | None
    code_path: str
    language: Literal["python", "java"]
    code_sha256: Sha
    syntax_status: Literal["PASSED", "FAILED", "NOT_RUN"]
    functional_check_status: Literal["PASSED", "FAILED", "NOT_RUN"]
    functional_check_evidence: str | None
    raw_output_ref: str
    license_or_authorization_ref: str
    redistribution_allowed: bool
    privacy_status: Literal["PUBLIC_AUTHORIZED", "LOCAL_RESTRICTED", "SYNTHETIC"]
    synthetic: bool
    split: Split


class PairRelation(Record):
    sample_a: Identifier
    sample_b: Identifier
    claimed_relation: Relation
    review_status: Literal["NOT_REVIEWED", "CONFLICT", "AGREED"]
    reviewer_ids: list[Identifier]
    reviewer_types: list[Literal["HUMAN", "AI", "UNSPECIFIED"]]
    reviewer_independence_confirmed: bool
    reviewed_code_sha256: list[Sha]
    label_evidence_ref: str | None
    independence_evidence_ref: str | None
    reviewed_at: str | None
    template_only_shared_upstream_confirmed: bool

    @field_validator("reviewed_at")
    @classmethod
    def aware_review_date(cls, value):
        if value is not None and datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is None:
            raise ValueError("Review time must include timezone")
        return value


class Provenance(Record):
    status: Literal["UNREGISTERED", "FROZEN"]
    registered_at: str | None
    plan_ref: str | None
    config_sha256: Sha | None
    split_preregistered: bool
    user_study_consent_ref: str | None


class Corpus(Record):
    protocol_version: Literal["ai-convergence-1.0"]
    dataset_version: Identifier
    provenance: Provenance
    questions: list[Question] = Field(min_length=1, max_length=200)
    sessions: list[GenerationSession] = Field(max_length=1000)
    artifacts: list[Artifact] = Field(min_length=2, max_length=1000)
    pair_relations: list[PairRelation] = Field(max_length=10000)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_file(root: Path, value: str, *, limit=4_000_000):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Portable relative local file reference required")
    relative = Path(value)
    if relative.is_absolute() or PureWindowsPath(value).drive or ".." in relative.parts:
        raise ValueError("Path traversal or absolute path rejected")
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        raise ValueError("Missing local file or escaped root")
    if candidate.stat().st_size > limit:
        raise ValueError("Input file size limit exceeded")
    return candidate


def read_corpus(file: Path):
    if file.stat().st_size > 8_000_000:
        raise ValueError("Metadata size limit exceeded")
    try:
        return Corpus.model_validate(json.loads(file.read_text(encoding="utf-8")))
    except ValidationError as error:
        # Never echo input values, paths with identities, prompts or secret fields.
        locations = [".".join(map(str, e["loc"])) + ":" + e["type"] for e in error.errors()]
        raise ValueError("Metadata schema errors: " + "; ".join(locations)) from None


def unique(rows, field):
    indexed = {getattr(row, field): row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError("Duplicate record identity: " + field)
    return indexed


def write_json(file, value):
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def require_private_output(is_real, output):
    project = Path(__file__).resolve().parents[3]
    if is_real and not output.resolve().is_relative_to(project / "output"):
        raise ValueError("Real raw outputs must remain under ignored project/output, never public evidence")


def export_schemas(output):
    output.mkdir(parents=True, exist_ok=False)
    for name, model in {"question": Question, "generation_session": GenerationSession,
                        "artifact": Artifact, "pair_relation": PairRelation,
                        "provenance": Provenance, "corpus": Corpus}.items():
        write_json(output / (name + ".schema.json"), model.model_json_schema())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export schemas from executable Pydantic models; always offline")
    parser.add_argument("--schema-output", type=Path, required=True)
    args = parser.parse_args()
    export_schemas(args.schema_output.resolve())
