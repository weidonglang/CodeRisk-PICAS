from app.analyzers.problem_profile import calibrated_risk_score, risk_level_from_margin
from app.analyzers.token_similarity import analyze_token_pair
from app.schemas.analyze_schema import AnalyzeMockRequest


def _request(code_a: str, code_b: str, language: str = "python") -> AnalyzeMockRequest:
    return AnalyzeMockRequest.model_validate(
        {
            "taskId": 1,
            "question": {
                "id": 1,
                "title": "Scope-aware normalization",
                "description": "Compare nested functions while preserving lexical scope.",
            },
            "submissionA": {"id": 11, "language": language, "code": code_a},
            "submissionB": {"id": 12, "language": language, "code": code_b},
        }
    )


def test_risk_level_boundaries_follow_formula_spec() -> None:
    assert risk_level_from_margin(-0.100001) == "LOW"
    assert risk_level_from_margin(-0.10) == "MEDIUM"
    assert risk_level_from_margin(-0.000001) == "MEDIUM"
    assert risk_level_from_margin(0.0) == "ELEVATED"
    assert risk_level_from_margin(0.099999) == "ELEVATED"
    assert risk_level_from_margin(0.10) == "HIGH"


def test_calibrated_risk_score_is_bounded_and_uses_margin_scale() -> None:
    assert calibrated_risk_score(-1.0, 0.40) == 0.0
    assert calibrated_risk_score(0.0, 0.40) == 0.5
    assert calibrated_risk_score(0.10, 0.40) == 0.75
    assert calibrated_risk_score(1.0, 0.40) == 1.0


def test_python_nested_scopes_keep_shadowed_parameters_separate() -> None:
    code_a = """\
def outer(value):
    total = value
    def inner(value):
        total = value + 1
        return total
    return inner(total)
"""
    code_b = """\
def process(number):
    answer = number
    def helper(item):
        local = item + 1
        return local
    return helper(answer)
"""
    result = analyze_token_pair(_request(code_a, code_b)).model_dump(by_alias=True)

    assert result["canonicalTokenSimilarity"] == 1.0
    mapping = next(item for item in result["evidence"] if item["evidenceType"] == "IDENTIFIER_MAPPING")
    parameter_scopes = {
        item["scopePath"]
        for item in mapping["metadata"]["mappings"]
        if item["mappingType"] == "PARAMETER"
    }
    assert len(parameter_scopes) == 2
    assert mapping["metadata"]["mappingCoverage"] == 1.0
    assert mapping["metadata"]["mappingConsistency"] == 1.0


def test_java_variable_function_and_parameter_renames_are_stable() -> None:
    code_a = "class Main { int sum(int first, int second) { int total = first + second; return total; } }"
    code_b = "class Main { int add(int left, int right) { int answer = left + right; return answer; } }"
    result = analyze_token_pair(_request(code_a, code_b, "java")).model_dump(by_alias=True)

    assert result["canonicalTokenSimilarity"] > result["tokenSimilarity"]
    mapping = next(item for item in result["evidence"] if item["evidenceType"] == "IDENTIFIER_MAPPING")
    mapping_types = {item["mappingType"] for item in mapping["metadata"]["mappings"]}
    assert {"VARIABLE", "FUNCTION", "PARAMETER"} <= mapping_types
