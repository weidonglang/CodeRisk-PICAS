from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    get_settings.cache_clear()

    def override_settings():
        from app.config import Settings

        upload_root = tmp_path / "uploads"
        artifact_root = tmp_path / "artifacts"
        upload_root.mkdir(exist_ok=True)
        artifact_root.mkdir(exist_ok=True)
        return Settings(
            analysis_version="test",
            config_version="test",
            upload_root=str(upload_root),
            artifact_root=str(artifact_root),
        )

    app = create_app()
    app.dependency_overrides[get_settings] = override_settings
    return TestClient(app)


def test_health_returns_analysis_envelope(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.get("/internal/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["result"]["status"] == "UP"
    assert payload["analysisVersion"] == "test"


def test_mock_rejects_paths_outside_upload_root(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    payload = {
        "taskId": 1,
        "question": {"id": 1, "title": "A+B"},
        "submissionA": {"id": 11, "language": "java", "rawCodePath": str(tmp_path / "uploads" / "a.java")},
        "submissionB": {"id": 12, "language": "java", "rawCodePath": str(tmp_path / "outside" / "b.java")},
    }

    response = client.post("/internal/analyze/mock", json=payload)

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["errorCode"] == "ANALYSIS_REQUEST_INVALID"


def test_mock_marks_result_as_mock(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    upload_root = tmp_path / "uploads"
    payload = {
        "taskId": 1,
        "question": {"id": 1, "title": "A+B"},
        "submissionA": {"id": 11, "language": "java", "rawCodePath": str(upload_root / "a.java")},
        "submissionB": {"id": 12, "language": "python", "rawCodePath": str(upload_root / "b.py")},
    }

    response = client.post("/internal/analyze/mock", json=payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["result"]["isMock"] is True
    assert payload["result"]["riskLevel"] == "LOW"


def test_pair_identical_java_has_high_token_similarity(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    upload_root = tmp_path / "uploads"
    upload_root.mkdir(exist_ok=True)
    left = upload_root / "left.java"
    right = upload_root / "right.java"
    code = "class Main { public static void main(String[] args) { System.out.println(1); } }"
    left.write_text(code, encoding="utf-8")
    right.write_text(code, encoding="utf-8")

    response = client.post("/internal/analyze/pair", json=_pair_payload(left, right, "java"))

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["isMock"] is False
    assert result["tokenSimilarity"] == 1.0
    assert result["riskLevel"] == "HIGH"
    fragments = result["evidence"][0]["metadata"]["fragments"]
    assert fragments
    assert fragments[0]["submissionAStartLine"] == 1
    assert fragments[0]["submissionBStartLine"] == 1


def test_pair_java_comments_do_not_reduce_similarity(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    upload_root = tmp_path / "uploads"
    upload_root.mkdir(exist_ok=True)
    left = upload_root / "left.java"
    right = upload_root / "right.java"
    left.write_text("class Main { int add(int a, int b) { return a + b; } }", encoding="utf-8")
    right.write_text(
        "/* header */ class Main { // inline\n int add(int a, int b) { return a + b; } }",
        encoding="utf-8",
    )

    response = client.post("/internal/analyze/pair", json=_pair_payload(left, right, "java"))

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["tokenSimilarity"] == 1.0
    assert result["isMock"] is False
    fragments = result["evidence"][0]["metadata"]["fragments"]
    assert fragments[0]["submissionAStartLine"] >= 1
    assert fragments[0]["submissionBStartLine"] >= 1


def test_pair_different_python_code_has_low_token_similarity(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    upload_root = tmp_path / "uploads"
    upload_root.mkdir(exist_ok=True)
    left = upload_root / "left.py"
    right = upload_root / "right.py"
    left.write_text("def solve(a, b):\n    return a + b\n", encoding="utf-8")
    right.write_text("import sys\nfor line in sys.stdin:\n    print(line[::-1])\n", encoding="utf-8")

    response = client.post("/internal/analyze/pair", json=_pair_payload(left, right, "python"))

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["tokenSimilarity"] < 0.35
    assert result["riskLevel"] == "LOW"


def test_pair_python_ast_similarity_and_evidence(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    upload_root = tmp_path / "uploads"
    upload_root.mkdir(exist_ok=True)
    left = upload_root / "left.py"
    right = upload_root / "right.py"
    code = "def solve(a, b):\n    total = a + b\n    return total\n"
    left.write_text(code, encoding="utf-8")
    right.write_text(code, encoding="utf-8")

    response = client.post("/internal/analyze/pair", json=_pair_payload(left, right, "python"))

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["astSimilarity"] == 1.0
    assert any(item["evidenceType"] == "AST_STRUCTURE_MATCH" for item in result["evidence"])


def test_pair_python_parse_failure_falls_back_without_ast_evidence(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    upload_root = tmp_path / "uploads"
    upload_root.mkdir(exist_ok=True)
    left = upload_root / "left.py"
    right = upload_root / "right.py"
    left.write_text("def broken(:\n    return 1\n", encoding="utf-8")
    right.write_text("def solve():\n    return 1\n", encoding="utf-8")

    response = client.post("/internal/analyze/pair", json=_pair_payload(left, right, "python"))

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["astSimilarity"] == 0.0
    evidence_types = {item["evidenceType"] for item in result["evidence"]}
    assert "PARSER_WARNING" in evidence_types
    assert "AST_STRUCTURE_MATCH" not in evidence_types
    assert "CANONICAL_TOKEN_MATCH" not in evidence_types
    assert "IDENTIFIER_MAPPING" not in evidence_types
    assert result["canonicalTokenSimilarity"] == 0.0
    assert result["identifierMappingSimilarity"] == 0.0
    assert result["weightedSimilarityScore"] == result["tokenSimilarity"]
    metric_weights = {item["name"]: item["weight"] for item in result["metrics"]}
    assert metric_weights["TOKEN_SIMILARITY"] == 1.0
    assert metric_weights["AST_SIMILARITY"] == 0.0
    assert metric_weights["CANONICAL_TOKEN_SIMILARITY"] == 0.0
    assert metric_weights["IDENTIFIER_MAPPING_SIMILARITY"] == 0.0


def test_pair_java_identifier_rename_improves_canonical_similarity(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    upload_root = tmp_path / "uploads"
    upload_root.mkdir(exist_ok=True)
    left = upload_root / "left.java"
    right = upload_root / "right.java"
    left.write_text(
        "class Main { int sum(int first, int second) { int total = first + second; return total; } }",
        encoding="utf-8",
    )
    right.write_text(
        "class Main { int add(int a, int b) { int answer = a + b; return answer; } }",
        encoding="utf-8",
    )

    response = client.post("/internal/analyze/pair", json=_pair_payload(left, right, "java"))

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["canonicalTokenSimilarity"] > result["tokenSimilarity"]
    assert result["canonicalTokenSimilarity"] > 0.80
    evidence_types = {item["evidenceType"] for item in result["evidence"]}
    assert "IDENTIFIER_MAPPING" in evidence_types
    assert "CANONICAL_TOKEN_MATCH" in evidence_types


def test_python_scope_aware_function_parameter_and_variable_rename_golden_case(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    left = """\
def first(left):
    value = left + 1
    return value

def second(right):
    value = right * 2
    return value
"""
    right = """\
def alpha(item):
    result = item + 1
    return result

def beta(number):
    doubled = number * 2
    return doubled
"""
    result = _post_inline_pair(client, "python", left, right)

    assert result["canonicalTokenSimilarity"] == 1.0
    assert result["canonicalTokenSimilarity"] > result["tokenSimilarity"]
    assert result["identifierMappingSimilarity"] == 1.0
    mapping_evidence = next(item for item in result["evidence"] if item["evidenceType"] == "IDENTIFIER_MAPPING")
    mappings = mapping_evidence["metadata"]["mappings"]
    assert {item["mappingType"] for item in mappings} >= {"VARIABLE", "FUNCTION", "PARAMETER"}
    value_mappings = [item for item in mappings if item["submissionAName"] == "value"]
    assert len(value_mappings) == 2
    assert len({item["scopePath"] for item in value_mappings}) == 2
    assert mapping_evidence["metadata"]["mappingCoverage"] == 1.0


def test_java_parameter_rename_is_classified_as_parameter(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    left = "class Main { int sum(int first, int second) { return first + second; } }"
    right = "class Main { int add(int a, int b) { return a + b; } }"
    result = _post_inline_pair(client, "java", left, right)

    assert result["canonicalTokenSimilarity"] == 1.0
    mapping_evidence = next(item for item in result["evidence"] if item["evidenceType"] == "IDENTIFIER_MAPPING")
    parameter_mappings = [
        item for item in mapping_evidence["metadata"]["mappings"]
        if item["mappingType"] == "PARAMETER"
    ]
    assert len(parameter_mappings) == 2


def test_problem_profile_produces_different_thresholds_for_different_questions(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    simple = {
        "question": {
            "id": 1,
            "title": "Array Sum",
            "description": "Read integers and output their sum.",
            "inputFormat": "n and n integers",
            "outputFormat": "one integer",
            "constraintsText": "1 <= n <= 100",
        }
    }
    complex_question = {
        "question": {
            "id": 2,
            "title": "Dynamic shortest paths on a graph",
            "description": (
                "Given a weighted directed graph, answer shortest path queries after edge updates. "
                "Design an efficient graph algorithm and explain unreachable states and overflow handling. " * 4
            ),
            "inputFormat": "n m q, followed by edges, updates, and queries on separate lines",
            "outputFormat": "one shortest path result for every query",
            "constraintsText": "1 <= n <= 200000\n1 <= m <= 400000\n1 <= q <= 200000\n0 <= w <= 1000000000",
        }
    }

    simple_result = client.post("/internal/problem/score", json=simple).json()["result"]
    complex_result = client.post("/internal/problem/score", json=complex_question).json()["result"]

    assert simple_result["problemProfile"]["naturalSimilarityRisk"] > complex_result["problemProfile"]["naturalSimilarityRisk"]
    assert simple_result["problemProfile"]["recommendedBaseThreshold"] > complex_result["problemProfile"]["recommendedBaseThreshold"]
    assert simple_result["thresholdAdjustment"]["formulaVersion"] == "FORMULA_SPEC_V1"


def test_pair_uses_margin_calibration_formula(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    code = "def solve(value):\n    return value + 1\n"
    result = _post_inline_pair(client, "python", code, code)

    expected = min(1.0, max(0.0, 0.5 + result["riskMargin"] / result["marginScale"]))
    assert result["calibratedRiskScore"] == round(expected, 6)
    assert result["formulaVersion"] == "FORMULA_SPEC_V1"
    assert result["dynamicThreshold"] == result["thresholdAdjustment"]["finalThreshold"]
    assert "problemProfile" in result


def _pair_payload(left: Path, right: Path, language: str) -> dict:
    return {
        "taskId": 1,
        "question": {"id": 1, "title": "A+B"},
        "submissionA": {"id": 11, "language": language, "rawCodePath": str(left)},
        "submissionB": {"id": 12, "language": language, "rawCodePath": str(right)},
    }


def _post_inline_pair(client: TestClient, language: str, left: str, right: str) -> dict:
    payload = {
        "taskId": 1,
        "question": {
            "id": 1,
            "title": "A+B",
            "description": "Read two integers and output their sum.",
            "inputFormat": "two integers",
            "outputFormat": "one integer",
            "constraintsText": "-100 <= a, b <= 100",
        },
        "submissionA": {"id": 11, "language": language, "code": left},
        "submissionB": {"id": 12, "language": language, "code": right},
    }
    response = client.post("/internal/analyze/pair", json=payload)
    assert response.status_code == 200
    return response.json()["result"]
