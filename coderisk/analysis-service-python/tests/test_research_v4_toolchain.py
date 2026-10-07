import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "experiment"
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from add_research_v4_case import _parser, build_entry  # noqa: E402
from calibrate_dynamic_threshold import calibrate  # noqa: E402
from research_v4_jplag import prepare_inputs  # noqa: E402


def test_case_entry_helper_hashes_files_and_lists_pending_fields(tmp_path: Path) -> None:
    dataset_root = tmp_path / "research-v4"
    sample_root = dataset_root / "samples/manual"
    sample_root.mkdir(parents=True)
    (sample_root / "a.py").write_text("def solve(x):\n    return x + 1\n", encoding="utf-8")
    (sample_root / "b.py").write_text("def process(value):\n    return value + 1\n", encoding="utf-8")
    args = _parser().parse_args([
        "--dataset-root", str(dataset_root),
        "--pair-id", "MANUAL-PAIR-1",
        "--problem-id", "MANUAL-PROBLEM-1",
        "--problem-type", "simple_io",
        "--problem-group", "G1",
        "--dataset-split", "validation",
        "--source-id", "MANUAL-SOURCE-1",
        "--source-type", "manual",
        "--experiment-label", "TRANSFORMED",
        "--case-type", "HUMAN_REWRITE",
        "--language-a", "python",
        "--language-b", "python",
        "--code-a", "samples/manual/a.py",
        "--code-b", "samples/manual/b.py",
    ])

    entry, pending = build_entry(args, dataset_root)

    assert entry["pair_id"] == "MANUAL-PAIR-1"
    assert entry["code_a_sha256"].startswith("sha256:")
    assert entry["source_type"] == "manual"
    assert entry["eligible_for_core_metrics"] is False
    assert {"title", "description", "license_or_authorization"} <= set(pending)


def test_jplag_preparation_aligns_manifest_pairs_and_records_exclusions(tmp_path: Path) -> None:
    result = prepare_inputs(
        ROOT / "experiment/datasets/research-v4/dataset.json",
        tmp_path / "jplag",
    )

    assert result["datasetPairCount"] == 91
    assert len(result["alignmentRows"]) == 72
    assert len(result["excludedRows"]) == 19
    assert (tmp_path / "jplag/alignment_manifest.csv").is_file()
    assert (tmp_path / "jplag/excluded_pairs.csv").is_file()
    assert (tmp_path / "jplag/input/java").is_dir()
    assert (tmp_path / "jplag/input/python").is_dir()


def test_dynamic_calibration_uses_validation_then_evaluates_test(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.csv"
    rows = [
        {"pairId": "V-P", "split": "validation", "label": "TRANSFORMED", "eligibleForCoreMetrics": True, "weightedSimilarityScore": 0.72, "dynamicThreshold": 0.75},
        {"pairId": "V-N", "split": "validation", "label": "NATURAL_SIMILAR", "eligibleForCoreMetrics": True, "weightedSimilarityScore": 0.60, "dynamicThreshold": 0.75},
        {"pairId": "T-P", "split": "test", "label": "SUSPICIOUS", "eligibleForCoreMetrics": True, "weightedSimilarityScore": 0.72, "dynamicThreshold": 0.75},
        {"pairId": "T-N", "split": "test", "label": "INDEPENDENT", "eligibleForCoreMetrics": True, "weightedSimilarityScore": 0.50, "dynamicThreshold": 0.75},
    ]
    with predictions.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = calibrate(
        predictions,
        tmp_path / "calibration",
        offsets=[-0.05, 0.0, 0.05],
        run_id="CAL-TEST",
        formula_version="FORMULA_SPEC_V1",
        algorithm_version="picas-v2-rule-1.0",
        dataset_version="seed-test",
        random_seed=7,
    )

    assert report["selectedParameters"]["selectionSplit"] == "validation"
    assert report["selectedParameters"]["testSetUsedForSelection"] is False
    assert report["selectedParameters"]["productionFormulaChanged"] is False
    assert {"precision", "recall", "f1", "falsePositiveRate", "naturalSimilarityFpr", "suspiciousRecall"} <= set(
        report["testMetrics"]["validationCalibratedOffset"]
    )
    assert (tmp_path / "calibration/calibration_report.md").is_file()
