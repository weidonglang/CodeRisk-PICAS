import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "experiment"
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from research_v4_dataset import load_research_dataset, validate_cases  # noqa: E402


MANIFEST = ROOT / "experiment/datasets/research-v4/dataset.json"
RUNNER = ROOT / "experiment/run_research_v4.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("coderisk_research_v4", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_research_dataset_aggregates_existing_shards_without_split_leakage() -> None:
    manifest, cases, report = load_research_dataset(MANIFEST)

    assert manifest["status"] == "SYNTHETIC_SEED_READY_AWAITING_REAL_DATA"
    assert len(cases) == 91
    assert report["valid"] is True
    assert report["validationCaseCount"] == 41
    assert report["testCaseCount"] == 50
    assert report["problemOverlap"] == []
    assert report["sourceOverlap"] == []
    assert report["exactCodeOverlapCases"] == []
    assert report["nonPreregisteredSplitCaseCount"] == 7
    assert report["targetGap"] == 0
    assert report["missingCaseTypes"] == []
    assert {gap["value"] for gap in report["coverageGaps"]} == {"manual", "ai_assisted", "external"}
    assert {
        "pair_id", "dataset_split", "source_type", "code_a_sha256", "code_b_sha256",
        "experiment_label", "case_type", "language", "problem_id", "dataset_version",
    } <= set(cases[0])


def test_research_dataset_rejects_problem_and_source_leakage() -> None:
    manifest, cases, _ = load_research_dataset(MANIFEST)
    leaked = copy.deepcopy(cases)
    validation_case = next(case for case in leaked if case["split"] == "validation")
    test_case = next(case for case in leaked if case["split"] == "test")
    test_case["problem_id"] = validation_case["problem_id"]
    test_case["source_id"] = validation_case["source_id"]

    report = validate_cases(manifest, leaked)

    assert report["valid"] is False
    assert report["problemOverlap"] == [validation_case["problem_id"]]
    assert report["sourceOverlap"] == [validation_case["source_id"]]


def test_unverified_ai_rewrite_cannot_enter_core_metrics() -> None:
    manifest, cases, _ = load_research_dataset(MANIFEST)
    ai_case = copy.deepcopy(cases[0])
    ai_case["case_id"] = "TEST-AI-UNVERIFIED"
    ai_case["pair_id"] = "TEST-AI-UNVERIFIED"
    ai_case["problem_id"] = "TEST-AI-PROBLEM"
    ai_case["source_id"] = "TEST-AI-SOURCE"
    ai_case["case_type"] = "AI_REWRITE"
    ai_case["eligible_for_core_metrics"] = True
    ai_case["provenance"] = {"model_name": "unspecified"}

    report = validate_cases(manifest, [*cases, ai_case])

    assert report["valid"] is False
    assert any("Eligible AI_REWRITE" in error for error in report["errors"])


def test_research_runner_writes_unified_matrix(tmp_path: Path, monkeypatch) -> None:
    runner = _load_runner()
    config = json.loads((ROOT / "configs/experiments/research_v4.json").read_text(encoding="utf-8"))
    config["outputRoot"] = str(tmp_path / "artifacts")
    config_path = tmp_path / "research-v4-config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [str(RUNNER), "--config", str(config_path), "--run-id", "test-research-v4"])

    assert runner.main() == 0

    output = tmp_path / "artifacts/test-research-v4"
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((output / "metrics_summary.json").read_text(encoding="utf-8"))
    report = (output / "research_report.md").read_text(encoding="utf-8")
    assert manifest["caseCount"] == 91
    assert manifest["targetGap"] == 0
    assert manifest["problemOverlap"] == []
    assert manifest["experimentalMetricsProductionWeight"] == 0.0
    assert manifest["productionFormulaChanged"] is False
    assert manifest["calibrationSelectionSplit"] == "validation"
    assert manifest["calibrationTestUsedForSelection"] is False
    assert summary["crossLanguage"]["productionScoreIntegration"] is False
    assert (output / "paper_tables/table_cross_language.csv").is_file()
    assert (output / "paper_tables/table_dynamic_threshold_calibration.csv").is_file()
    assert (output / "paper_tables/table_jplag_vs_picas.csv").is_file()
    assert (output / "paper_tables/table_baseline_comparison.csv").is_file()
    assert (output / "case_analysis/common_structure_cases.csv").is_file()
    assert (output / "dataset_validation/case_index.csv").is_file()
    assert "not a real benchmark" in report
