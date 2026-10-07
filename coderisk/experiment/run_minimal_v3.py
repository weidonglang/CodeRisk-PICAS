from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / "analysis-service-python"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from app.analyzers.token_similarity import analyze_token_pair  # noqa: E402
from app.schemas.analyze_schema import AnalyzeMockRequest  # noqa: E402


POSITIVE_LABELS = {"SIMILAR", "SUSPICIOUS", "TRANSFORMED"}
NEGATIVE_LABELS = {"INDEPENDENT", "NATURAL_SIMILAR"}
VALID_LABELS = POSITIVE_LABELS | NEGATIVE_LABELS | {"UNCERTAIN"}
VALID_CASE_TYPES = {
    "ORIGINAL_COPY",
    "VARIABLE_RENAME",
    "PARAMETER_RENAME",
    "FUNCTION_RENAME",
    "FORMAT_COMMENT_CHANGE",
    "LOCAL_REORDER",
    "SPLIT_MERGE",
    "CROSSLANG_REWRITE",
    "AI_REWRITE",
    "NATURAL_TEMPLATE",
    "INDEPENDENT_SOLUTION",
}
REQUIRED_CASE_FIELDS = {
    "case_id",
    "problem_id",
    "problem_type",
    "problem_group",
    "split",
    "source_id",
    "experiment_label",
    "case_type",
    "language",
    "dataset_version",
    "question",
    "code_a",
    "code_b",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the CodeRisk V3 minimal reproducible experiment matrix.")
    parser.add_argument("--config", default="configs/experiments/minimal_v3.json")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    config_path = resolve_path(args.config)
    config = read_json(config_path)
    dataset_path = resolve_path(config["dataset"])
    dataset = read_json(dataset_path)
    split_manifest = validate_dataset(dataset, config)
    random.seed(int(config["randomSeed"]))

    run_id = args.run_id or f"{config['experimentId']}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    output_dir = resolve_path(config["outputRoot"]) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    start_clock = time.perf_counter()

    predictions: list[dict[str, Any]] = []
    parser_failures: list[dict[str, Any]] = []
    for index, case in enumerate(dataset["cases"], start=1):
        case_start = time.perf_counter()
        result = analyze_case(index, case)
        runtime_ms = round((time.perf_counter() - case_start) * 1000.0, 3)
        row = {
            "caseId": case["case_id"],
            "caseType": case["case_type"],
            "label": case["experiment_label"],
            "problemId": case["problem_id"],
            "problemType": case["problem_type"],
            "problemGroup": case["problem_group"],
            "split": case["split"],
            "sourceId": case["source_id"],
            "language": case["language"],
            "datasetVersion": case["dataset_version"],
            "tokenSimilarity": result["tokenSimilarity"],
            "astSimilarity": result["astSimilarity"],
            "canonicalTokenSimilarity": result["canonicalTokenSimilarity"],
            "identifierMappingSimilarity": result["identifierMappingSimilarity"],
            "weightedSimilarityScore": result["weightedSimilarityScore"],
            "dynamicThreshold": result["dynamicThreshold"],
            "riskMargin": result["riskMargin"],
            "calibratedRiskScore": result["calibratedRiskScore"],
            "riskLevel": result["riskLevel"],
            "exceedThreshold": result["exceedThreshold"],
            "runtimeMs": runtime_ms,
        }
        predictions.append(row)
        evidence_types = {item["evidenceType"] for item in result["evidence"]}
        if "PARSER_WARNING" in evidence_types:
            parser_failures.append({**row, "failureType": "PARSER_FALLBACK"})

    fixed_thresholds = [float(value) for value in config["fixedThresholds"]]
    validation_rows = [row for row in predictions if row["split"] == config["validationSplit"]]
    test_rows = [row for row in predictions if row["split"] == config["evaluationSplit"]]
    calibration = select_validation_threshold(validation_rows, fixed_thresholds, config["calibrationPolicy"])
    e1_rows = fixed_vs_dynamic(test_rows, fixed_thresholds)
    e2_rows = raw_vs_canonical(test_rows)
    e3_rows = fusion_comparison(test_rows)
    e4_rows = ablation_comparison(test_rows)
    failure_rows, borderline_rows = failure_analysis(test_rows, float(config["borderlineMargin"]))
    test_case_ids = {row["caseId"] for row in test_rows}
    test_parser_failures = [row for row in parser_failures if row["caseId"] in test_case_ids]
    failure_rows.extend(test_parser_failures)
    metrics_by_problem_type = grouped_metrics(test_rows, "problemType")

    finished_at = datetime.now(timezone.utc)
    manifest = {
        "experimentId": config["experimentId"],
        "experimentName": config["experimentName"],
        "runId": run_id,
        "formulaVersion": config["formulaVersion"],
        "algorithmVersion": config["algorithmVersion"],
        "datasetId": dataset["dataset_id"],
        "datasetVersion": dataset["dataset_version"],
        "randomSeed": config["randomSeed"],
        "gitCommit": local_version(),
        "configFile": relative(config_path),
        "datasetFile": relative(dataset_path),
        "startTime": started_at.isoformat(),
        "endTime": finished_at.isoformat(),
        "durationMs": round((time.perf_counter() - start_clock) * 1000.0, 3),
        "machineInfo": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor() or "unknown",
        },
        "caseCount": len(predictions),
        "classificationCaseCount": sum(1 for row in predictions if row["label"] in POSITIVE_LABELS | NEGATIVE_LABELS),
        "validationCaseCount": len(validation_rows),
        "testCaseCount": len(test_rows),
        "validationProblemCount": len(split_manifest["validationProblemIds"]),
        "testProblemCount": len(split_manifest["testProblemIds"]),
        "calibrationPolicy": config["calibrationPolicy"],
        "resultPath": relative(output_dir),
    }
    summary = {
        "run": manifest,
        "validationCalibration": calibration,
        "splitManifest": split_manifest,
        "E1_fixedVsDynamic": e1_rows,
        "E2_rawVsCanonical": summarize_e2(e2_rows),
        "E3_fusion": e3_rows,
        "E4_ablation": e4_rows,
        "E5_failureAnalysis": {
            "failureCount": len(failure_rows),
            "borderlineCount": len(borderline_rows),
            "parserFallbackCount": len(test_parser_failures),
        },
        "metricsByProblemType": metrics_by_problem_type,
    }

    write_json(output_dir / "run_manifest.json", manifest)
    write_json(output_dir / "metrics_summary.json", summary)
    write_json(output_dir / "split_manifest.json", split_manifest)
    write_json(output_dir / "validation_calibration.json", calibration)
    write_csv(output_dir / "predictions.csv", predictions)
    write_csv(output_dir / "fixed_vs_dynamic.csv", e1_rows)
    write_csv(output_dir / "raw_vs_canonical.csv", e2_rows)
    write_csv(output_dir / "fusion_comparison.csv", e3_rows)
    write_csv(output_dir / "ablation.csv", e4_rows)
    write_csv(output_dir / "failure_cases.csv", failure_rows)
    write_csv(output_dir / "borderline_cases.csv", borderline_rows)
    write_csv(output_dir / "metrics_by_problem_type.csv", metrics_by_problem_type)
    (output_dir / "experiment_report.md").write_text(
        build_report(manifest, calibration, e1_rows, e2_rows, e3_rows, e4_rows, failure_rows, borderline_rows),
        encoding="utf-8",
    )
    write_json(resolve_path(config["outputRoot"]) / "latest.json", {"runId": run_id, "resultPath": relative(output_dir)})
    print(json.dumps({"runId": run_id, "outputDir": str(output_dir), "caseCount": len(predictions)}, ensure_ascii=False))
    return 0


def analyze_case(index: int, case: dict[str, Any]) -> dict[str, Any]:
    question_data = case["question"]
    question = {
        "id": index,
        "title": question_data["title"],
        "description": question_data["description"],
        "inputFormat": question_data.get("input_format", ""),
        "outputFormat": question_data.get("output_format", ""),
        "constraintsText": question_data.get("constraints_text", ""),
    }
    request = AnalyzeMockRequest.model_validate(
        {
            "taskId": index,
            "question": question,
            "submissionA": {"id": index * 2, "language": case["language"], "code": case["code_a"]},
            "submissionB": {"id": index * 2 + 1, "language": case["language"], "code": case["code_b"]},
            "config": {"mode": "PICAS_EXPERIMENTAL", "baseThreshold": 0.68},
        }
    )
    return analyze_token_pair(request).model_dump(by_alias=True)


def fixed_vs_dynamic(rows: list[dict[str, Any]], thresholds: list[float]) -> list[dict[str, Any]]:
    results = []
    classified = classified_rows(rows)
    for threshold in thresholds:
        results.append(metric_row(f"FIXED_{threshold:.2f}", classified, lambda row, t=threshold: row["weightedSimilarityScore"] >= t))
    results.append(metric_row("PICAS_DYNAMIC", classified, lambda row: row["weightedSimilarityScore"] >= row["dynamicThreshold"]))
    return results


def raw_vs_canonical(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "caseId": row["caseId"],
            "caseType": row["caseType"],
            "label": row["label"],
            "rawTokenSimilarity": row["tokenSimilarity"],
            "canonicalTokenSimilarity": row["canonicalTokenSimilarity"],
            "canonicalGain": round(row["canonicalTokenSimilarity"] - row["tokenSimilarity"], 6),
            "retentionRatio": round(row["canonicalTokenSimilarity"] / max(row["tokenSimilarity"], 1e-9), 6),
        }
        for row in rows
        if row["caseType"] in {"VARIABLE_RENAME", "PARAMETER_RENAME", "FUNCTION_RENAME"}
    ]


def fusion_comparison(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = classified_rows(rows)
    methods = {
        "TOKEN_ONLY": lambda row: (row["tokenSimilarity"], 0.80),
        "TOKEN_AST": lambda row: (
            (row["tokenSimilarity"] + row["astSimilarity"]) / 2.0 if row["astSimilarity"] > 0 else row["tokenSimilarity"],
            0.80,
        ),
        "PICAS_STANDARD": lambda row: (row["weightedSimilarityScore"], row["dynamicThreshold"]),
    }
    return [score_method(name, classified, scorer) for name, scorer in methods.items()]


def ablation_comparison(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = classified_rows(rows)
    methods = {
        "PICAS_NO_DT": lambda row: (row["weightedSimilarityScore"], 0.80),
        "PICAS_NO_CANON": lambda row: (
            0.55 * row["tokenSimilarity"] + 0.45 * row["astSimilarity"] if row["astSimilarity"] > 0 else row["tokenSimilarity"],
            row["dynamicThreshold"],
        ),
        "PICAS_FULL": lambda row: (row["weightedSimilarityScore"], row["dynamicThreshold"]),
    }
    return [score_method(name, classified, scorer) for name, scorer in methods.items()]


def failure_analysis(rows: list[dict[str, Any]], margin: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    failures = []
    borderline = []
    for row in classified_rows(rows):
        expected = row["label"] in POSITIVE_LABELS
        predicted = bool(row["exceedThreshold"])
        if expected != predicted:
            failures.append({**row, "failureType": "FALSE_NEGATIVE" if expected else "FALSE_POSITIVE"})
        if abs(float(row["riskMargin"])) <= margin:
            borderline.append({**row, "failureType": "BORDERLINE"})
    return failures, borderline


def metric_row(name: str, rows: list[dict[str, Any]], predictor) -> dict[str, Any]:
    labels = [row["label"] in POSITIVE_LABELS for row in rows]
    predictions = [bool(predictor(row)) for row in rows]
    metrics = classification_metrics(labels, predictions)
    natural_rows = [row for row in rows if row["label"] == "NATURAL_SIMILAR"]
    natural_fp = sum(1 for row in natural_rows if predictor(row))
    metrics.update(
        {
            "method": name,
            "naturalSimilarityFalsePositives": natural_fp,
            "naturalSimilarityCaseCount": len(natural_rows),
            "naturalSimilarityFpr": round(natural_fp / max(len(natural_rows), 1), 6),
        }
    )
    return metrics


def score_method(name: str, rows: list[dict[str, Any]], scorer) -> dict[str, Any]:
    labels = [row["label"] in POSITIVE_LABELS for row in rows]
    predictions = []
    for row in rows:
        score, threshold = scorer(row)
        predictions.append(score >= threshold)
    return {"method": name, **classification_metrics(labels, predictions)}


def classification_metrics(labels: list[bool], predictions: list[bool]) -> dict[str, Any]:
    tp = sum(1 for actual, predicted in zip(labels, predictions) if actual and predicted)
    tn = sum(1 for actual, predicted in zip(labels, predictions) if not actual and not predicted)
    fp = sum(1 for actual, predicted in zip(labels, predictions) if not actual and predicted)
    fn = sum(1 for actual, predicted in zip(labels, predictions) if actual and not predicted)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    return {
        "sampleCount": len(labels),
        "truePositive": tp,
        "trueNegative": tn,
        "falsePositive": fp,
        "falseNegative": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "accuracy": round((tp + tn) / max(len(labels), 1), 6),
        "falsePositiveRate": round(fp / max(fp + tn, 1), 6),
        "falseNegativeRate": round(fn / max(fn + tp, 1), 6),
    }


def summarize_e2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "caseCount": len(rows),
        "meanRawTokenSimilarity": mean([row["rawTokenSimilarity"] for row in rows]),
        "meanCanonicalTokenSimilarity": mean([row["canonicalTokenSimilarity"] for row in rows]),
        "meanCanonicalGain": mean([row["canonicalGain"] for row in rows]),
    }


def mean(values: list[float]) -> float:
    return round(sum(values) / max(len(values), 1), 6)


def classified_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["label"] in POSITIVE_LABELS | NEGATIVE_LABELS]


def validate_dataset(dataset: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if dataset.get("dataset_version") != config.get("datasetVersion"):
        raise ValueError("Dataset version does not match the experiment config")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Dataset cases must be a non-empty list")
    case_ids: set[str] = set()
    source_splits: dict[str, str] = {}
    problems_by_split: dict[str, set[str]] = {"validation": set(), "test": set()}
    for case in cases:
        missing = REQUIRED_CASE_FIELDS - set(case)
        if missing:
            raise ValueError(f"Case is missing required fields: {sorted(missing)}")
        if case["case_id"] in case_ids:
            raise ValueError(f"Duplicate case_id: {case['case_id']}")
        case_ids.add(case["case_id"])
        if case["dataset_version"] != dataset["dataset_version"]:
            raise ValueError(f"Case dataset version mismatch: {case['case_id']}")
        if case["experiment_label"] not in VALID_LABELS:
            raise ValueError(f"Unknown experiment_label: {case['experiment_label']}")
        if case["case_type"] not in VALID_CASE_TYPES:
            raise ValueError(f"Unknown case_type: {case['case_type']}")
        split = case["split"]
        if split not in problems_by_split:
            raise ValueError(f"Unsupported split: {split}")
        problems_by_split[split].add(case["problem_id"])
        previous_split = source_splits.setdefault(case["source_id"], split)
        if previous_split != split:
            raise ValueError(f"Source leakage across splits: {case['source_id']}")
    overlap = problems_by_split["validation"] & problems_by_split["test"]
    if overlap:
        raise ValueError(f"Problem leakage across splits: {sorted(overlap)}")
    return {
        "validationProblemIds": sorted(problems_by_split["validation"]),
        "testProblemIds": sorted(problems_by_split["test"]),
        "problemOverlap": [],
        "sourceOverlap": [],
        "validationCaseCount": sum(1 for case in cases if case["split"] == "validation"),
        "testCaseCount": sum(1 for case in cases if case["split"] == "test"),
    }


def select_validation_threshold(
    rows: list[dict[str, Any]], thresholds: list[float], policy: str
) -> dict[str, Any]:
    candidates = fixed_vs_dynamic(rows, thresholds)[:-1]
    selected = max(candidates, key=lambda row: (row["f1"], -row["falsePositiveRate"], row["recall"]))
    return {
        "policy": policy,
        "selectedFixedThreshold": float(selected["method"].removeprefix("FIXED_")),
        "selectionMetric": "validation F1, then lower FPR, then recall",
        "validationMetrics": selected,
        "productionDynamicFormulaChanged": False,
    }


def grouped_metrics(rows: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    groups = sorted({str(row[group_key]) for row in rows})
    result = []
    for group in groups:
        members = [row for row in rows if str(row[group_key]) == group]
        metrics = metric_row(
            "PICAS_DYNAMIC",
            classified_rows(members),
            lambda row: row["weightedSimilarityScore"] >= row["dynamicThreshold"],
        )
        result.append({"groupName": group_key, "groupValue": group, **metrics})
    return result


def build_report(manifest, calibration, e1, e2, e3, e4, failures, borderline) -> str:
    dynamic = next(row for row in e1 if row["method"] == "PICAS_DYNAMIC")
    fixed_rows = [row for row in e1 if row["method"].startswith("FIXED_")]
    e2_summary = summarize_e2(e2)
    improved_baselines = [
        row["method"] for row in fixed_rows
        if dynamic["naturalSimilarityFpr"] < row["naturalSimilarityFpr"]
    ]
    threshold_statement = (
        "本次最小合成数据运行中，动态阈值相对 "
        + "、".join(improved_baselines)
        + " 降低了 natural-similar 误报；同时动态阈值召回率为 "
        + str(dynamic["recall"])
        + "，说明当前规则仍偏保守，不能省略失败案例与后续校准。"
        if improved_baselines
        else "本次最小合成数据运行未观察到动态阈值的 natural-similar 误报下降，需扩大数据并校准。"
    )
    canonical_statement = (
        "改名样本中 canonical token 的平均相似度高于 raw token。"
        if e2_summary["meanCanonicalTokenSimilarity"] > e2_summary["meanRawTokenSimilarity"]
        else "本次改名样本未显示 canonical token 的平均优势，需检查规范化或样本。"
    )
    lines = [
        "# PICAS V3 最小实验报告",
        "",
        "> 本报告来自脚本真实运行的合成样本，不代表大规模基准结论，也不用于直接判定纪律问题。",
        "",
        "## 运行信息",
        "",
        f"- Run ID: `{manifest['runId']}`",
        f"- Formula: `{manifest['formulaVersion']}`",
        f"- Algorithm: `{manifest['algorithmVersion']}`",
        f"- Dataset: `{manifest['datasetVersion']}`",
        f"- Random seed: `{manifest['randomSeed']}`",
        f"- Local version: `{manifest['gitCommit']}`",
        f"- Cases: `{manifest['caseCount']}`",
        f"- Validation/Test: `{manifest['validationCaseCount']}` / `{manifest['testCaseCount']}`",
        f"- Problem split: `{manifest['validationProblemCount']}` validation / `{manifest['testProblemCount']}` test, overlap `0`",
        f"- Validation-selected fixed baseline: `{calibration['selectedFixedThreshold']}`",
        "- Production dynamic formula changed during calibration: `false`",
        "",
        "## E1 固定阈值 vs 动态阈值",
        "",
        threshold_statement,
        "",
        markdown_table(e1),
        "",
        "## E2 Raw token vs Canonical token",
        "",
        canonical_statement,
        "",
        markdown_table([e2_summary]),
        "",
        "## E3 多维融合",
        "",
        markdown_table(e3),
        "",
        "## E4 消融",
        "",
        markdown_table(e4),
        "",
        "## E5 失败与边界案例",
        "",
        f"- Failure rows: `{len(failures)}`",
        f"- Borderline rows: `{len(borderline)}`",
        "- 逐例记录见 `failure_cases.csv` 与 `borderline_cases.csv`。",
        "",
        "## 边界",
        "",
        "该实验使用 problem-level 隔离的合成小样本，只验证技术链路和趋势，不包含 CFG、DFG、跨语言 IR 或 AI 改写增强。外部基线仅提供适配接口，不计入本次结果。",
    ]
    return "\n".join(lines) + "\n"


def markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    headers = list(rows[0].keys())
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def local_version() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True, timeout=3
        ).strip()
    except Exception:
        return os.getenv("CODERISK_LOCAL_VERSION", "workspace-no-git-20260620")


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
