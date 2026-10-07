import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "experiment" / "run_minimal_v3.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("coderisk_minimal_experiment", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_minimal_v3_experiment_writes_reproducible_artifacts(tmp_path: Path, monkeypatch) -> None:
    runner = load_runner()
    config = json.loads((ROOT / "configs" / "experiments" / "minimal_v3.json").read_text(encoding="utf-8"))
    config["outputRoot"] = str(tmp_path / "artifacts")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [str(RUNNER), "--config", str(config_path), "--run-id", "test-run"])

    assert runner.main() == 0

    output = tmp_path / "artifacts" / "test-run"
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((output / "metrics_summary.json").read_text(encoding="utf-8"))
    report = (output / "experiment_report.md").read_text(encoding="utf-8")

    assert manifest["formulaVersion"] == "FORMULA_SPEC_V1"
    assert manifest["algorithmVersion"] == "picas-v2-rule-1.0"
    assert manifest["randomSeed"] == 20260620
    assert manifest["caseCount"] == 36
    assert manifest["validationCaseCount"] == 15
    assert manifest["testCaseCount"] == 21
    assert manifest["validationProblemCount"] == 5
    assert manifest["testProblemCount"] == 5
    assert summary["E2_rawVsCanonical"]["meanCanonicalTokenSimilarity"] > summary["E2_rawVsCanonical"]["meanRawTokenSimilarity"]
    assert summary["validationCalibration"]["productionDynamicFormulaChanged"] is False
    assert summary["splitManifest"]["problemOverlap"] == []
    assert summary["splitManifest"]["sourceOverlap"] == []
    assert (output / "predictions.csv").is_file()
    assert (output / "split_manifest.json").is_file()
    assert (output / "validation_calibration.json").is_file()
    assert (output / "metrics_by_problem_type.csv").is_file()
    assert (output / "failure_cases.csv").is_file()
    assert (output / "borderline_cases.csv").is_file()
    assert "不代表大规模基准结论" in report


def test_dataset_validator_rejects_problem_leakage() -> None:
    runner = load_runner()
    config = json.loads((ROOT / "configs" / "experiments" / "minimal_v3.json").read_text(encoding="utf-8"))
    dataset = json.loads((ROOT / config["dataset"]).read_text(encoding="utf-8"))
    test_case = next(case for case in dataset["cases"] if case["split"] == "test")
    validation_case = next(case for case in dataset["cases"] if case["split"] == "validation")
    test_case["problem_id"] = validation_case["problem_id"]

    try:
        runner.validate_dataset(dataset, config)
    except ValueError as error:
        assert "Problem leakage" in str(error)
    else:
        raise AssertionError("Expected problem leakage to be rejected")
