import json
from pathlib import Path

import pytest

from app.analyzers.token_similarity import analyze_token_pair
from app.schemas.analyze_schema import AnalyzeMockRequest


GOLDEN_ROOT = Path(__file__).resolve().parents[2] / "tests" / "golden_cases"
CASE_FILES = sorted(GOLDEN_ROOT.glob("*/case.json"))


@pytest.mark.parametrize("case_file", CASE_FILES, ids=lambda path: path.parent.name)
def test_rename_golden_case(case_file: Path) -> None:
    case = json.loads(case_file.read_text(encoding="utf-8"))
    expected = case["expected"]
    code_a = (case_file.parent / case["codeA"]).read_text(encoding="utf-8")
    code_b = (case_file.parent / case["codeB"]).read_text(encoding="utf-8")
    request = AnalyzeMockRequest.model_validate(
        {
            "taskId": 1,
            "question": {
                "id": 1,
                "title": case["caseId"],
                "description": (case_file.parent / "problem.md").read_text(encoding="utf-8"),
            },
            "submissionA": {"id": 11, "language": case["language"], "code": code_a},
            "submissionB": {"id": 12, "language": case["language"], "code": code_b},
        }
    )

    result = analyze_token_pair(request).model_dump(by_alias=True)
    assert result["canonicalTokenSimilarity"] >= expected["canonicalSimilarityMin"]
    if expected.get("canonicalGreaterThanRaw"):
        assert result["canonicalTokenSimilarity"] > result["tokenSimilarity"]
    mapping_evidence = next(item for item in result["evidence"] if item["evidenceType"] == "IDENTIFIER_MAPPING")
    mapping_types = {item["mappingType"] for item in mapping_evidence["metadata"]["mappings"]}
    assert mapping_types >= set(expected["mappingTypes"])
