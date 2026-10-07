from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.schemas.analyze_schema import QuestionPayload


FORMULA_VERSION = "FORMULA_SPEC_V1"
FEATURE_VERSION = "pf-rule-v1.0"
MARGIN_SCALE = 0.40


@dataclass(frozen=True)
class ProblemProfile:
    description_length: int
    io_field_count: int
    constraint_count: int
    sample_count: int
    reference_line_count: int
    reference_function_count: int
    reference_cyclomatic_complexity: float
    api_call_count: int
    data_structure_count: int
    difficulty_score: float
    solution_space_score: float
    template_risk_score: float
    natural_similarity_risk: float
    recommended_base_threshold: float
    confidence: float
    explanation: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "featureVersion": FEATURE_VERSION,
            "descriptionLength": self.description_length,
            "ioFieldCount": self.io_field_count,
            "constraintCount": self.constraint_count,
            "sampleCount": self.sample_count,
            "referenceLineCount": self.reference_line_count,
            "referenceFunctionCount": self.reference_function_count,
            "referenceCyclomaticComplexity": self.reference_cyclomatic_complexity,
            "apiCallCount": self.api_call_count,
            "dataStructureCount": self.data_structure_count,
            "difficultyScore": self.difficulty_score,
            "solutionSpaceScore": self.solution_space_score,
            "templateRiskScore": self.template_risk_score,
            "naturalSimilarityRisk": self.natural_similarity_risk,
            "recommendedBaseThreshold": self.recommended_base_threshold,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class ThresholdResult:
    dynamic_threshold: float
    base_threshold: float
    difficulty_adjustment: float
    solution_space_adjustment: float
    template_risk_adjustment: float
    natural_similarity_adjustment: float
    historical_distribution_adjustment: float
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "baseThreshold": self.base_threshold,
            "difficultyAdjustment": self.difficulty_adjustment,
            "solutionSpaceAdjustment": self.solution_space_adjustment,
            "templateRiskAdjustment": self.template_risk_adjustment,
            "naturalSimilarityAdjustment": self.natural_similarity_adjustment,
            "historicalDistributionAdjustment": self.historical_distribution_adjustment,
            "finalThreshold": self.dynamic_threshold,
            "formulaVersion": FORMULA_VERSION,
            "explanation": self.explanation,
        }


TEMPLATE_TERMS = {
    "sum", "count", "maximum", "minimum", "average", "sort", "reverse", "palindrome",
    "print", "read", "input", "output", "数组求和", "计数", "最大值", "最小值", "排序",
    "反转", "回文", "输入", "输出", "统计",
}
COMPLEXITY_TERMS = {
    "graph", "tree", "dynamic programming", "shortest path", "topological", "backtracking",
    "segment tree", "union find", "binary search", "图", "树", "动态规划", "最短路", "拓扑",
    "回溯", "线段树", "并查集", "二分",
}
DATA_STRUCTURE_TERMS = {
    "array", "list", "set", "map", "queue", "stack", "heap", "graph", "tree",
    "数组", "列表", "集合", "映射", "队列", "栈", "堆", "图", "树",
}


def build_problem_profile(question: QuestionPayload, config: dict[str, Any] | None = None) -> ProblemProfile:
    config = config or {}
    text = "\n".join(
        part for part in (
            question.title,
            question.description,
            question.input_format,
            question.output_format,
            question.constraints_text,
        ) if part
    )
    lowered = text.lower()
    description_length = len(question.description.strip())
    io_field_count = _non_empty_line_count(question.input_format) + _non_empty_line_count(question.output_format)
    constraint_count = _constraint_count(question.constraints_text)
    sample_count = len(re.findall(r"(?i)(sample|example|样例|示例)", text))
    template_hits = _term_hits(lowered, TEMPLATE_TERMS)
    complexity_hits = _term_hits(lowered, COMPLEXITY_TERMS)
    data_structure_count = _term_hits(lowered, DATA_STRUCTURE_TERMS)

    length_factor = _clamp(description_length / 1200.0)
    io_factor = _clamp(io_field_count / 8.0)
    constraint_factor = _clamp(constraint_count / 8.0)
    complexity_factor = _clamp(complexity_hits / 4.0)
    structure_factor = _clamp(data_structure_count / 5.0)

    difficulty = _clamp(
        0.24 * length_factor
        + 0.18 * io_factor
        + 0.24 * constraint_factor
        + 0.24 * complexity_factor
        + 0.10 * structure_factor
    )
    solution_space = _clamp(
        0.10
        + 0.45 * difficulty
        + 0.25 * complexity_factor
        + 0.20 * structure_factor
        - 0.15 * _clamp(template_hits / 4.0)
    )
    template_risk = _clamp(
        0.20
        + 0.45 * _clamp(template_hits / 4.0)
        + 0.20 * (1.0 - difficulty)
        + 0.15 * (1.0 - solution_space)
    )
    natural_similarity = _clamp(
        0.45 * template_risk
        + 0.30 * (1.0 - solution_space)
        + 0.25 * (1.0 - difficulty)
    )

    confidence = 0.78 if description_length >= 80 and io_field_count >= 2 else 0.62
    reasons = _profile_reasons(difficulty, solution_space, template_risk, natural_similarity, template_hits)
    profile = ProblemProfile(
        description_length=description_length,
        io_field_count=io_field_count,
        constraint_count=constraint_count,
        sample_count=sample_count,
        reference_line_count=int(config.get("referenceLineCount", 0) or 0),
        reference_function_count=int(config.get("referenceFunctionCount", 0) or 0),
        reference_cyclomatic_complexity=float(config.get("referenceCyclomaticComplexity", 0.0) or 0.0),
        api_call_count=int(config.get("apiCallCount", 0) or 0),
        data_structure_count=data_structure_count,
        difficulty_score=_rounded(difficulty),
        solution_space_score=_rounded(solution_space),
        template_risk_score=_rounded(template_risk),
        natural_similarity_risk=_rounded(natural_similarity),
        recommended_base_threshold=0.0,
        confidence=confidence,
        explanation=reasons,
    )
    threshold = calculate_dynamic_threshold(profile, config)
    return ProblemProfile(**{**profile.__dict__, "recommended_base_threshold": threshold.dynamic_threshold})


def calculate_dynamic_threshold(profile: ProblemProfile, config: dict[str, Any] | None = None) -> ThresholdResult:
    config = config or {}
    base = _config_number(config, "baseThreshold", 0.68, 0.10, 0.99)
    difficulty_weight = _config_number(config, "difficultyThresholdWeight", 0.06, 0.0, 0.30)
    solution_weight = _config_number(config, "solutionSpaceThresholdWeight", 0.04, 0.0, 0.30)
    template_weight = _config_number(config, "templateRiskThresholdWeight", 0.08, 0.0, 0.30)
    natural_weight = _config_number(config, "naturalSimilarityThresholdWeight", 0.12, 0.0, 0.30)

    difficulty_adjustment = -difficulty_weight * profile.difficulty_score
    solution_adjustment = -solution_weight * profile.solution_space_score
    template_adjustment = template_weight * profile.template_risk_score
    natural_adjustment = natural_weight * profile.natural_similarity_risk
    final = _clamp(
        base + difficulty_adjustment + solution_adjustment + template_adjustment + natural_adjustment,
        0.50,
        0.95,
    )
    explanation = (
        "题目画像规则版：自然相似与模板化风险提高复核阈值，题目难度与解法空间扩大则降低阈值；"
        "各因素只通过动态阈值校准，不从综合相似度中重复扣分。"
    )
    return ThresholdResult(
        dynamic_threshold=_rounded(final),
        base_threshold=_rounded(base),
        difficulty_adjustment=_rounded(difficulty_adjustment),
        solution_space_adjustment=_rounded(solution_adjustment),
        template_risk_adjustment=_rounded(template_adjustment),
        natural_similarity_adjustment=_rounded(natural_adjustment),
        historical_distribution_adjustment=0.0,
        explanation=explanation,
    )


def calibrated_risk_score(risk_margin: float, margin_scale: float = MARGIN_SCALE) -> float:
    safe_scale = margin_scale if margin_scale > 0 else MARGIN_SCALE
    return _rounded(_clamp(0.5 + risk_margin / safe_scale))


def risk_level_from_margin(risk_margin: float) -> str:
    if risk_margin < -0.10:
        return "LOW"
    if risk_margin < 0:
        return "MEDIUM"
    if risk_margin < 0.10:
        return "ELEVATED"
    return "HIGH"


def _profile_reasons(
    difficulty: float,
    solution_space: float,
    template_risk: float,
    natural_similarity: float,
    template_hits: int,
) -> dict[str, Any]:
    difficulty_reason = "题面与约束显示出较多结构要求" if difficulty >= 0.55 else "题面结构和约束相对直接"
    solution_reason = "可能存在多种独立实现路径" if solution_space >= 0.55 else "可行解法空间相对集中"
    template_reason = "命中常见模板关键词" if template_hits else "未明显命中常见模板关键词"
    natural_reason = "独立实现也可能自然相似" if natural_similarity >= 0.60 else "自然相似风险处于较低或中等水平"
    return {
        "difficultyReasons": [difficulty_reason],
        "solutionSpaceReasons": [solution_reason],
        "templateRiskReasons": [template_reason],
        "naturalSimilarityReasons": [natural_reason],
        "ruleVersion": FEATURE_VERSION,
        "scores": {
            "difficulty": _rounded(difficulty),
            "solutionSpace": _rounded(solution_space),
            "templateRisk": _rounded(template_risk),
            "naturalSimilarity": _rounded(natural_similarity),
        },
    }


def _constraint_count(text: str) -> int:
    if not text.strip():
        return 0
    comparisons = len(re.findall(r"<=|>=|<|>|≤|≥|=", text))
    lines = _non_empty_line_count(text)
    return max(lines, comparisons // 2, 1)


def _non_empty_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def _term_hits(text: str, terms: set[str]) -> int:
    return sum(1 for term in terms if term in text)


def _config_number(config: dict[str, Any], key: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(config.get(key, default))
    except (TypeError, ValueError):
        value = default
    return _clamp(value, minimum, maximum)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return min(maximum, max(minimum, value))


def _rounded(value: float) -> float:
    return round(value, 6)
