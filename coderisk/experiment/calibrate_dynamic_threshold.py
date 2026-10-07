from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


POSITIVE_LABELS = {"SIMILAR", "SUSPICIOUS", "TRANSFORMED"}
NEGATIVE_LABELS = {"INDEPENDENT", "NATURAL_SIMILAR"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate an experiment-only dynamic-threshold offset on validation only.")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--formula-version", default="FORMULA_SPEC_V1")
    parser.add_argument("--algorithm-version", default="picas-v2-rule-1.0")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--random-seed", type=int, required=True)
    parser.add_argument("--offsets", default="-0.08,-0.04,0.0,0.04,0.08")
    args = parser.parse_args()
    offsets = [float(value) for value in args.offsets.split(",")]
    result = calibrate(
        args.predictions.resolve(),
        args.output_dir.resolve(),
        offsets=offsets,
        run_id=args.run_id,
        formula_version=args.formula_version,
        algorithm_version=args.algorithm_version,
        dataset_version=args.dataset_version,
        random_seed=args.random_seed,
    )
    print(json.dumps(result["selectedParameters"], ensure_ascii=False))
    return 0


def calibrate(
    predictions_path: Path,
    output_dir: Path,
    *,
    offsets: list[float],
    run_id: str,
    formula_version: str,
    algorithm_version: str,
    dataset_version: str,
    random_seed: int,
) -> dict[str, Any]:
    with predictions_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    eligible = [
        row for row in rows
        if _boolean(row.get("eligibleForCoreMetrics")) and row.get("label") in POSITIVE_LABELS | NEGATIVE_LABELS
    ]
    validation_rows = [row for row in eligible if row.get("split") == "validation"]
    test_rows = [row for row in eligible if row.get("split") == "test"]
    if not validation_rows or not test_rows:
        raise ValueError("Calibration requires non-empty eligible validation and test splits")

    candidates = [
        {"thresholdOffset": offset, **_evaluate(validation_rows, offset)}
        for offset in offsets
    ]
    selected = max(
        candidates,
        key=lambda row: (
            row["f1"],
            -row["naturalSimilarityFpr"],
            row["suspiciousRecall"],
            row["recall"],
            -abs(row["thresholdOffset"]),
        ),
    )
    selected_offset = float(selected["thresholdOffset"])
    production_test = _evaluate(test_rows, 0.0)
    calibrated_test = _evaluate(test_rows, selected_offset)
    selected_parameters = {
        "runId": run_id,
        "formulaVersion": formula_version,
        "algorithmVersion": algorithm_version,
        "datasetVersion": dataset_version,
        "randomSeed": random_seed,
        "parameter": "dynamicThresholdOffset",
        "previousValue": 0.0,
        "selectedValue": selected_offset,
        "selectionSplit": "validation",
        "evaluationSplit": "test",
        "selectionPolicy": "validation F1, lower natural-similar FPR, suspicious recall, recall, smaller absolute offset",
        "testSetUsedForSelection": False,
        "productionFormulaChanged": False,
        "experimentOnly": True,
    }
    report = {
        "selectedParameters": selected_parameters,
        "validationCandidates": candidates,
        "selectedValidationMetrics": selected,
        "testMetrics": {
            "productionDynamicThreshold": production_test,
            "validationCalibratedOffset": calibrated_test,
        },
        "caseCounts": {
            "validation": len(validation_rows),
            "test": len(test_rows),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "calibration_report.json", report)
    _write_json(output_dir / "selected_parameters.json", selected_parameters)
    _write_csv(output_dir / "validation_candidates.csv", candidates)
    _write_csv(output_dir / "test_evaluation.csv", [
        {"method": "PRODUCTION_DYNAMIC", "thresholdOffset": 0.0, **production_test},
        {"method": "VALIDATION_CALIBRATED", "thresholdOffset": selected_offset, **calibrated_test},
    ])
    (output_dir / "calibration_report.md").write_text(_markdown(report), encoding="utf-8")
    return report


def _evaluate(rows: list[dict[str, str]], offset: float) -> dict[str, Any]:
    actual = [row["label"] in POSITIVE_LABELS for row in rows]
    predicted = [
        float(row["weightedSimilarityScore"]) >= _clamp(float(row["dynamicThreshold"]) + offset, 0.50, 0.95)
        for row in rows
    ]
    tp = sum(a and p for a, p in zip(actual, predicted))
    tn = sum(not a and not p for a, p in zip(actual, predicted))
    fp = sum(not a and p for a, p in zip(actual, predicted))
    fn = sum(a and not p for a, p in zip(actual, predicted))
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    natural = [(row, prediction) for row, prediction in zip(rows, predicted) if row["label"] == "NATURAL_SIMILAR"]
    suspicious = [(row, prediction) for row, prediction in zip(rows, predicted) if row["label"] == "SUSPICIOUS"]
    return {
        "sampleCount": len(rows),
        "truePositive": tp,
        "trueNegative": tn,
        "falsePositive": fp,
        "falseNegative": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "falsePositiveRate": round(fp / max(fp + tn, 1), 6),
        "falseNegativeRate": round(fn / max(fn + tp, 1), 6),
        "naturalSimilarityFpr": round(sum(prediction for _, prediction in natural) / max(len(natural), 1), 6),
        "suspiciousRecall": round(sum(prediction for _, prediction in suspicious) / max(len(suspicious), 1), 6),
    }


def _markdown(report: dict[str, Any]) -> str:
    selected = report["selectedParameters"]
    test = report["testMetrics"]
    lines = [
        "# Research V4 Dynamic Threshold Calibration",
        "",
        "> Synthetic seed pre-experiment. Selection uses validation only; test is evaluated once and cannot be used to revise parameters.",
        "",
        f"- Run: `{selected['runId']}`",
        f"- Formula/algorithm: `{selected['formulaVersion']}` / `{selected['algorithmVersion']}`",
        f"- Dataset: `{selected['datasetVersion']}`",
        f"- Selected offset: `{selected['selectedValue']}`",
        "- Test used for selection: `false`",
        "- Production formula changed: `false`",
        "",
        "## Test evaluation",
        "",
        _table([
            {"method": "PRODUCTION_DYNAMIC", **test["productionDynamicThreshold"]},
            {"method": "VALIDATION_CALIBRATED", **test["validationCalibratedOffset"]},
        ]),
        "",
        "These values validate the calibration workflow only. Synthetic seed results must not be presented as final threshold evidence.",
        "",
    ]
    return "\n".join(lines)


def _table(rows: list[dict[str, Any]]) -> str:
    headers = list(rows[0])
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |" for row in rows)
    return "\n".join(lines)


def _boolean(value: Any) -> bool:
    return str(value).lower() in {"true", "1", "yes"}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
