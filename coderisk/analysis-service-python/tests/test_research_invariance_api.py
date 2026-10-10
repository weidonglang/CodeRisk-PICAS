"""The production API must preserve located warnings and existing formula contracts."""
import pytest

from test_health_and_mock import build_client, _pair_payload


@pytest.mark.parametrize("code,reason", [
    ("def f(value):\n    return globals()['value']\n", "PYTHON_DYNAMIC_NAME_ACCESS_UNSUPPORTED"),
    ("def f(value):\n    return value\nalias=f\nalias(value=1)", "PYTHON_INDIRECT_KEYWORD_CALL_UNSUPPORTED"),
    ("obj.method(value=1)", "PYTHON_ATTRIBUTE_KEYWORD_CALL_UNSUPPORTED"),
    ("def f(value, **options):\n    return value\nf(value=1)", "PYTHON_VARIADIC_KEYWORD_CALL_UNSUPPORTED"),
])
def test_new_warning_categories_use_existing_api_schema_and_raw_weight(tmp_path, code, reason):
    client = build_client(tmp_path)
    a, b = tmp_path / "uploads/a.py", tmp_path / "uploads/b.py"
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text(code, encoding="utf-8")
    b.write_text("def solve(number):\n    return number + 1\n", encoding="utf-8")
    response = client.post("/internal/analyze/pair", json=_pair_payload(a, b, "python"))
    assert response.status_code == 200
    result = response.json()["result"]
    warning = next(item for item in result["evidence"] if item["evidenceType"] == "PARSER_WARNING")
    assert warning["metadata"]["normalizationReasonA"].startswith(reason + ":")
    assert "line" in warning["metadata"]["normalizationReasonA"]
    assert result["weightedSimilarityScore"] == result["tokenSimilarity"]
    assert not {"CANONICAL_TOKEN_MATCH", "IDENTIFIER_MAPPING"} & {item["evidenceType"] for item in result["evidence"]}


def test_direct_keyword_rename_reaches_metrics_and_original_line_evidence(tmp_path):
    client = build_client(tmp_path)
    a, b = tmp_path / "uploads/a.py", tmp_path / "uploads/b.py"
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text("def fold(value):\n    return value + 1\nfold(value=2)\n", encoding="utf-8")
    b.write_text("def process(number):\n    return number + 1\nprocess(number=2)\n", encoding="utf-8")
    response = client.post("/internal/analyze/pair", json=_pair_payload(a, b, "python"))
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["canonicalTokenSimilarity"] == result["identifierMappingSimilarity"] == 1
    evidence = next(item for item in result["evidence"] if item["evidenceType"] == "IDENTIFIER_MAPPING")
    mapping = next(item for item in evidence["metadata"]["mappings"] if item["submissionAName"] == "value")
    assert mapping["occurrenceA"] == mapping["occurrenceB"] == 3
    assert mapping["submissionALine"] == mapping["submissionBLine"] == 1
    metrics = {item["name"]: item["weight"] for item in result["metrics"]}
    assert metrics["CANONICAL_TOKEN_SIMILARITY"] == 0.45
    assert metrics["IDENTIFIER_MAPPING_SIMILARITY"] == 0.15
