"""Production API checks using self-authored fixtures, not dataset annotations."""
from pathlib import Path

import pytest

from test_health_and_mock import build_client, _pair_payload


@pytest.mark.parametrize("code,reason", [
    ("xs = [x for x in range(3)]\n", "PYTHON_COMPREHENSION_SCOPE_UNSUPPORTED"),
    ("value = 1\ndef f():\n    global value\n    return value\n", "PYTHON_GLOBAL_SCOPE_UNSUPPORTED"),
])
def test_parsed_but_unsupported_scope_is_explained_without_mapping(tmp_path: Path, code: str, reason: str):
    client = build_client(tmp_path)
    left, right = tmp_path / "uploads/a.py", tmp_path / "uploads/b.py"
    left.parent.mkdir(parents=True, exist_ok=True)
    left.write_text(code, encoding="utf-8")
    right.write_text("def solve(value):\n    return value + 1\n", encoding="utf-8")
    response = client.post("/internal/analyze/pair", json=_pair_payload(left, right, "python"))
    assert response.status_code == 200
    result = response.json()["result"]
    warning = next(e for e in result["evidence"] if e["evidenceType"] == "PARSER_WARNING")
    assert warning["metadata"]["normalizationReasonA"].startswith(reason + ":")
    assert warning["metadata"]["normalizationModeB"] == "scope-aware-python"
    assert result["canonicalTokenSimilarity"] == result["identifierMappingSimilarity"] == 0
    assert result["weightedSimilarityScore"] == result["tokenSimilarity"]
    assert not {"CANONICAL_TOKEN_MATCH", "IDENTIFIER_MAPPING"}.intersection(
        e["evidenceType"] for e in result["evidence"])
    weights = {m["name"]: m["weight"] for m in result["metrics"]}
    assert weights["TOKEN_SIMILARITY"] == 1
    assert weights["CANONICAL_TOKEN_SIMILARITY"] == weights["IDENTIFIER_MAPPING_SIMILARITY"] == 0
