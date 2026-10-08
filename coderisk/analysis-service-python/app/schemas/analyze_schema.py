from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuestionPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    description: str = ""
    input_format: str = Field(default="", alias="inputFormat")
    output_format: str = Field(default="", alias="outputFormat")
    constraints_text: str = Field(default="", alias="constraintsText")
    starter_language: str = Field(default='', alias='starterLanguage', max_length=16)
    starter_code: str = Field(default='', alias='starterCode', max_length=20000)
    starter_source: str = Field(default='', alias='starterSource', max_length=2000)

    @model_validator(mode='after')
    def validate_starter(self):
        if self.starter_code.strip() and (self.starter_language.lower() not in {'java', 'python', 'py', 'c', 'html', 'htm'} or not self.starter_source.strip()):
            raise ValueError('Shared starter code requires a supported language and a source reference')
        return self


class SubmissionPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    language: str
    file_name: str = Field(default="", alias="fileName")
    raw_code_path: str | None = Field(default=None, alias="rawCodePath")
    code: str | None = None
    language_version: str = Field(default='', alias='languageVersion', max_length=64, pattern=r'^[^\r\n]*$')


class AnalyzeMockRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: int | None = Field(default=None, alias="taskId")
    question: QuestionPayload
    submission_a: SubmissionPayload = Field(alias="submissionA")
    submission_b: SubmissionPayload = Field(alias="submissionB")
    config: dict[str, Any] = Field(default_factory=dict)


class ProblemScoreRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: QuestionPayload
    config: dict[str, Any] = Field(default_factory=dict)


class ProblemScoreResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_id: int = Field(alias="questionId")
    problem_profile: dict[str, Any] = Field(alias="problemProfile")
    threshold_adjustment: dict[str, Any] = Field(alias="thresholdAdjustment")


class MetricResult(BaseModel):
    name: str
    value: float
    weight: float
    explanation: str


class EvidenceResult(BaseModel):
    evidence_type: str = Field(alias="evidenceType")
    similarity_score: float = Field(alias="similarityScore")
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class AnalyzeMockResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: int | None = Field(default=None, alias="taskId")
    submission_a_id: int = Field(alias="submissionAId")
    submission_b_id: int = Field(alias="submissionBId")
    token_similarity: float = Field(default=0.42, alias="tokenSimilarity")
    ast_similarity: float = Field(default=0.0, alias="astSimilarity")
    canonical_token_similarity: float = Field(default=0.42, alias="canonicalTokenSimilarity")
    identifier_mapping_similarity: float = Field(default=0.0, alias="identifierMappingSimilarity")
    weighted_similarity_score: float = Field(default=0.42, alias="weightedSimilarityScore")
    dynamic_threshold: float = Field(default=0.80, alias="dynamicThreshold")
    risk_margin: float = Field(default=-0.38, alias="riskMargin")
    calibrated_risk_score: float = Field(default=0.18, alias="calibratedRiskScore")
    exceed_threshold: bool = Field(default=False, alias="exceedThreshold")
    margin_scale: float = Field(default=0.40, alias="marginScale")
    formula_version: str = Field(default="FORMULA_SPEC_V1", alias="formulaVersion")
    risk_level: str = Field(default="LOW", alias="riskLevel")
    problem_profile: dict[str, Any] = Field(default_factory=dict, alias="problemProfile")
    threshold_adjustment: dict[str, Any] = Field(default_factory=dict, alias="thresholdAdjustment")
    reason_summary: str = Field(
        default="Mock result for integration only; no disciplinary conclusion is produced.",
        alias="reasonSummary",
    )
    is_mock: bool = Field(default=True, alias="isMock")
    metrics: list[MetricResult] = Field(
        default_factory=lambda: [
            MetricResult(
                name="TokenSimilarity",
                value=0.42,
                weight=1.0,
                explanation="Fixed mock metric for V0 integration only.",
            )
        ]
    )
    evidence: list[EvidenceResult] = Field(
        default_factory=lambda: [
            EvidenceResult(
                evidenceType="REVIEW_NOTE",
                similarityScore=0.0,
                description="Mock result for backend/frontend integration; not an experiment result.",
                metadata={"isMock": True},
            )
        ]
    )
