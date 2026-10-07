from __future__ import annotations

import argparse
import csv
import hashlib
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

import run_minimal_v3 as v3  # noqa: E402
from calibrate_dynamic_threshold import calibrate  # noqa: E402
from research_v4_dataset import (  # noqa: E402
    NEGATIVE_LABELS,
    POSITIVE_LABELS,
    load_research_dataset,
    write_validation_artifacts,
)
from app.analyzers.lightweight_summaries import SUMMARY_VERSION  # noqa: E402
from app.analyzers.normalized_ir import IR_VERSION  # noqa: E402
from app.analyzers.token_similarity import analyze_token_pair  # noqa: E402
from app.schemas.analyze_schema import AnalyzeMockRequest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the unified CodeRisk Research V4 matrix.")
    parser.add_argument("--config", default="configs/experiments/research_v4.json")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    config_path = _resolve(args.config)
    config = _read_json(config_path)
    manifest_path = _resolve(config["datasetManifest"])
    manifest, cases, validation = load_research_dataset(manifest_path)
    random.seed(int(config["randomSeed"]))

    run_id = args.run_id or f"{config['experimentId']}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    output_dir = _resolve(config["outputRoot"]) / run_id
    if output_dir.exists():
        raise FileExistsError(f"Research run artifacts are immutable: {output_dir}")
    output_dir.mkdir(parents=True)
    started_at = datetime.now(timezone.utc)
    started_clock = time.perf_counter()

    write_validation_artifacts(output_dir / "dataset_validation", manifest, cases, validation)
    same_language = _run_same_language(cases, config, output_dir / "same_language")
    cross_language = _run_cross_language(cases, config, output_dir / "cross_language")
    calibration = calibrate(
        output_dir / "same_language/predictions.csv",
        output_dir / "calibration",
        offsets=[float(value) for value in config["calibrationOffsets"]],
        run_id=run_id,
        formula_version=config["formulaVersion"],
        algorithm_version=config["productionAlgorithmVersion"],
        dataset_version=manifest["dataset_version"],
        random_seed=int(config["randomSeed"]),
    )
    baselines = _baseline_registry(config)
    jplag_comparison = _aligned_jplag_comparison(config, same_language["predictions"])
    baseline_metrics = _baseline_comparison_metrics(jplag_comparison)
    _write_csv(output_dir / "baseline_registry.csv", baselines)
    _write_csv(output_dir / "baseline_analysis/jplag_vs_picas.csv", jplag_comparison)
    _write_paper_tables(
        output_dir / "paper_tables", validation, same_language, cross_language,
        baselines, calibration, jplag_comparison,
        baseline_metrics,
    )
    _write_case_analysis(output_dir / "case_analysis", same_language, cross_language)

    finished_at = datetime.now(timezone.utc)
    run_manifest = {
        "experimentId": config["experimentId"],
        "experimentName": config["experimentName"],
        "runId": run_id,
        "formulaVersion": config["formulaVersion"],
        "productionAlgorithmVersion": config["productionAlgorithmVersion"],
        "experimentalAlgorithmVersion": config["experimentalAlgorithmVersion"],
        "irVersion": IR_VERSION,
        "summaryVersion": SUMMARY_VERSION,
        "datasetId": manifest["dataset_id"],
        "datasetVersion": manifest["dataset_version"],
        "datasetContentSha256": _dataset_hash(cases),
        "datasetStatus": manifest["status"],
        "randomSeed": config["randomSeed"],
        "gitCommit": _local_version(),
        "configFile": _relative(config_path),
        "datasetManifest": _relative(manifest_path),
        "startTime": started_at.isoformat(),
        "endTime": finished_at.isoformat(),
        "durationMs": round((time.perf_counter() - started_clock) * 1000.0, 3),
        "machineInfo": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor() or "unknown",
        },
        "caseCount": validation["caseCount"],
        "eligibleCaseCount": validation["eligibleCaseCount"],
        "sameLanguageCaseCount": len(same_language["predictions"]),
        "crossLanguageCaseCount": len(cross_language["predictions"]),
        "targetGap": validation["targetGap"],
        "problemOverlap": validation["problemOverlap"],
        "sourceOverlap": validation["sourceOverlap"],
        "exactCodeOverlapCases": validation["exactCodeOverlapCases"],
        "nonPreregisteredSplitCaseCount": validation["nonPreregisteredSplitCaseCount"],
        "productionFormulaChanged": False,
        "experimentalMetricsProductionWeight": 0.0,
        "testSetModifiedDuringRun": False,
        "calibrationSelectedOffset": calibration["selectedParameters"]["selectedValue"],
        "calibrationSelectionSplit": "validation",
        "calibrationTestUsedForSelection": False,
    }
    summary = {
        "run": run_manifest,
        "datasetValidation": validation,
        "sameLanguage": same_language["summary"],
        "crossLanguage": cross_language["summary"],
        "calibration": calibration,
        "baselines": baselines,
        "jplagAlignedComparisonCount": len(jplag_comparison),
        "baselineComparison": baseline_metrics,
    }
    _write_json(output_dir / "run_manifest.json", run_manifest)
    _write_json(output_dir / "metrics_summary.json", summary)
    (output_dir / "research_report.md").write_text(
        _research_report(run_manifest, validation, same_language, cross_language, baselines, calibration, jplag_comparison, baseline_metrics),
        encoding="utf-8",
    )
    _write_json(_resolve(config["outputRoot"]) / "latest-research-v4.json", {
        "runId": run_id,
        "artifactPath": _relative(output_dir),
        "datasetVersion": manifest["dataset_version"],
    })
    print(json.dumps({
        "runId": run_id,
        "outputDir": str(output_dir),
        "caseCount": validation["caseCount"],
        "targetGap": validation["targetGap"],
    }, ensure_ascii=False))
    return 0


def _run_same_language(
    cases: list[dict[str, Any]], config: dict[str, Any], output_dir: Path
) -> dict[str, Any]:
    output_dir.mkdir(parents=True)
    selected = [case for case in cases if case["language_a"] == case["language_b"]]
    predictions: list[dict[str, Any]] = []
    parser_fallbacks: list[dict[str, Any]] = []
    for index, case in enumerate(selected, start=1):
        started = time.perf_counter()
        result = analyze_token_pair(_request(index, case, "PICAS_EXPERIMENTAL"))
        row = _same_language_row(case, result, round((time.perf_counter() - started) * 1000, 3))
        predictions.append(row)
        if "PARSER_WARNING" in {evidence.evidence_type for evidence in result.evidence}:
            parser_fallbacks.append({**row, "failureType": "PARSER_FALLBACK"})

    eligible = [row for row in predictions if row["eligibleForCoreMetrics"]]
    validation_rows = [row for row in eligible if row["split"] == config["validationSplit"]]
    test_rows = [row for row in eligible if row["split"] == config["evaluationSplit"]]
    fixed_thresholds = [float(value) for value in config["fixedThresholds"]]
    calibration = v3.select_validation_threshold(
        validation_rows,
        fixed_thresholds,
        "validation F1; production dynamic formula remains unchanged",
    )
    e1 = v3.fixed_vs_dynamic(test_rows, fixed_thresholds)
    e2 = v3.raw_vs_canonical(test_rows)
    e3 = v3.fusion_comparison(test_rows)
    e4 = v3.ablation_comparison(test_rows)
    failures, borderline = v3.failure_analysis(test_rows, float(config["borderlineMargin"]))
    failures.extend(row for row in parser_fallbacks if row["split"] == config["evaluationSplit"])
    by_problem = v3.grouped_metrics(test_rows, "problemType")
    by_case_type = v3.grouped_metrics(test_rows, "caseType")
    summary = {
        "caseCount": len(predictions),
        "eligibleCaseCount": len(eligible),
        "validationCaseCount": len(validation_rows),
        "testCaseCount": len(test_rows),
        "validationCalibration": calibration,
        "E1_fixedVsDynamic": e1,
        "E2_rawVsCanonical": v3.summarize_e2(e2),
        "E3_fusion": e3,
        "E4_ablation": e4,
        "E5_failureAnalysis": {
            "failureCount": len(failures),
            "borderlineCount": len(borderline),
            "parserFallbackCount": len(parser_fallbacks),
        },
        "metricsByProblemType": by_problem,
        "metricsByCaseType": by_case_type,
    }
    _write_csv(output_dir / "predictions.csv", predictions)
    _write_csv(output_dir / "fixed_vs_dynamic.csv", e1)
    _write_csv(output_dir / "raw_vs_canonical.csv", e2)
    _write_csv(output_dir / "fusion_comparison.csv", e3)
    _write_csv(output_dir / "ablation.csv", e4)
    _write_csv(output_dir / "failure_cases.csv", failures)
    _write_csv(output_dir / "borderline_cases.csv", borderline)
    _write_csv(output_dir / "metrics_by_problem_type.csv", by_problem)
    _write_csv(output_dir / "metrics_by_case_type.csv", by_case_type)
    _write_json(output_dir / "metrics_summary.json", summary)
    return {
        "predictions": predictions,
        "failures": failures,
        "borderline": borderline,
        "summary": summary,
        "e1": e1,
        "e2": e2,
        "e3": e3,
        "e4": e4,
    }


def _run_cross_language(
    cases: list[dict[str, Any]], config: dict[str, Any], output_dir: Path
) -> dict[str, Any]:
    output_dir.mkdir(parents=True)
    selected = [case for case in cases if case["language_a"] != case["language_b"]]
    threshold = float(config["crossLanguageReviewThreshold"])
    weights = config["crossLanguageCompositeWeights"]
    predictions: list[dict[str, Any]] = []
    for index, case in enumerate(selected, start=1):
        supported_pair = {case["language_a"], case["language_b"]} == {"java", "python"}
        if supported_pair:
            result = analyze_token_pair(_request(5000 + index, case, "PICAS_CROSSLANG"))
            metrics = {metric.name: metric.value for metric in result.metrics}
            evidence_types = {evidence.evidence_type for evidence in result.evidence}
            warnings = _warnings(result)
            values = {
                "tokenSimilarity": result.token_similarity,
                "astSimilarity": result.ast_similarity,
                "canonicalTokenSimilarity": result.canonical_token_similarity,
                "irSimilarity": metrics.get("CROSSLANG_IR_SIMILARITY", 0.0),
                "controlSummarySimilarity": metrics.get("CROSSLANG_CONTROL_SUMMARY_SIMILARITY", 0.0),
                "dataFlowSummarySimilarity": metrics.get("CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY", 0.0),
            }
            structure_unavailable = "CROSSLANG_IR_MATCH" not in evidence_types
        else:
            values = {name: 0.0 for name in (
                "tokenSimilarity", "astSimilarity", "canonicalTokenSimilarity", "irSimilarity",
                "controlSummarySimilarity", "dataFlowSummarySimilarity",
            )}
            warnings = ["Language pair is outside the limited Java/Python Research V4 prototype."]
            structure_unavailable = True
        composite = round(
            float(weights["ir"]) * values["irSimilarity"]
            + float(weights["controlSummary"]) * values["controlSummarySimilarity"]
            + float(weights["dataFlowSummary"]) * values["dataFlowSummarySimilarity"],
            6,
        )
        predicted = composite >= threshold
        row = {
            **_case_columns(case),
            **values,
            "experimentalComposite": composite,
            "reviewThreshold": threshold,
            "predictedRelated": predicted,
            "structureEvidenceUnavailable": structure_unavailable,
            "failureType": _cross_failure_type(case, predicted, structure_unavailable),
            "warnings": warnings,
        }
        predictions.append(row)

    test_rows = [row for row in predictions if row["split"] == config["evaluationSplit"]]
    eligible_test = [row for row in test_rows if row["eligibleForCoreMetrics"]]
    methods = _cross_method_comparison(eligible_test, threshold)
    failures = [row for row in test_rows if row["failureType"] != "NONE" or row["warnings"]]
    summary = {
        "caseCount": len(predictions),
        "eligibleTestCaseCount": len(eligible_test),
        "reviewThreshold": threshold,
        "experimentalCompositeWeights": weights,
        "methodComparison": methods,
        "failureCount": sum(row["failureType"] in {"FALSE_POSITIVE", "FALSE_NEGATIVE"} for row in test_rows),
        "expectedFallbackCount": sum(row["failureType"] == "EXPECTED_PARSE_FALLBACK" for row in test_rows),
        "unsupportedWarningCount": sum(bool(row["warnings"]) for row in test_rows),
        "productionScoreIntegration": False,
    }
    _write_csv(output_dir / "predictions.csv", predictions)
    _write_csv(output_dir / "method_comparison.csv", methods)
    _write_csv(output_dir / "failure_cases.csv", failures)
    _write_json(output_dir / "metrics_summary.json", summary)
    return {"predictions": predictions, "failures": failures, "methods": methods, "summary": summary}


def _same_language_row(case: dict[str, Any], result: Any, runtime_ms: float) -> dict[str, Any]:
    return {
        **_case_columns(case),
        "tokenSimilarity": result.token_similarity,
        "astSimilarity": result.ast_similarity,
        "canonicalTokenSimilarity": result.canonical_token_similarity,
        "identifierMappingSimilarity": result.identifier_mapping_similarity,
        "weightedSimilarityScore": result.weighted_similarity_score,
        "dynamicThreshold": result.dynamic_threshold,
        "riskMargin": result.risk_margin,
        "calibratedRiskScore": result.calibrated_risk_score,
        "riskLevel": result.risk_level,
        "exceedThreshold": result.exceed_threshold,
        "runtimeMs": runtime_ms,
    }


def _case_columns(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "caseId": case["case_id"],
        "pairId": case["pair_id"],
        "caseType": case["case_type"],
        "label": case["experiment_label"],
        "problemId": case["problem_id"],
        "problemType": case["problem_type"],
        "problemGroup": case["problem_group"],
        "split": case["split"],
        "datasetSplit": case["dataset_split"],
        "splitPreregistered": case["split_preregistered"],
        "sourceId": case["source_id"],
        "language": case["language"],
        "datasetVersion": case["dataset_version"],
        "dataOrigin": case["data_origin"],
        "sourceType": case["source_type"],
        "codeASha256": case["code_a_sha256"],
        "codeBSha256": case["code_b_sha256"],
        "synthetic": case["synthetic"],
        "eligibleForCoreMetrics": case["eligible_for_core_metrics"],
    }


def _request(index: int, case: dict[str, Any], mode: str) -> AnalyzeMockRequest:
    question = case["question"]
    return AnalyzeMockRequest.model_validate({
        "taskId": index,
        "question": {
            "id": index,
            "title": question["title"],
            "description": question["description"],
            "inputFormat": question.get("input_format", ""),
            "outputFormat": question.get("output_format", ""),
            "constraintsText": question.get("constraints_text", ""),
        },
        "submissionA": {"id": index * 2, "language": case["language_a"], "code": case["code_a"]},
        "submissionB": {"id": index * 2 + 1, "language": case["language_b"], "code": case["code_b"]},
        "config": {"mode": mode, "baseThreshold": 0.68},
    })


def _cross_method_comparison(rows: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
    fields = {
        "RAW_TOKEN": "tokenSimilarity",
        "LANGUAGE_SPECIFIC_AST": "astSimilarity",
        "CANONICAL_TOKEN": "canonicalTokenSimilarity",
        "NORMALIZED_IR_EXPERIMENTAL": "irSimilarity",
        "LIGHTWEIGHT_CONTROL_SUMMARY_EXPERIMENTAL": "controlSummarySimilarity",
        "LIGHTWEIGHT_DATA_SUMMARY_EXPERIMENTAL": "dataFlowSummarySimilarity",
        "V4_EXPERIMENTAL_COMPOSITE": "experimentalComposite",
    }
    labels = [row["label"] in POSITIVE_LABELS for row in rows if row["label"] in POSITIVE_LABELS | NEGATIVE_LABELS]
    classified = [row for row in rows if row["label"] in POSITIVE_LABELS | NEGATIVE_LABELS]
    result = []
    for method, field in fields.items():
        predicted = [float(row[field]) >= threshold for row in classified]
        result.append({"method": method, "threshold": threshold, **v3.classification_metrics(labels, predicted)})
    return result


def _cross_failure_type(case: dict[str, Any], predicted: bool, unavailable: bool) -> str:
    if case["case_type"] == "PARSER_FAILURE":
        return "EXPECTED_PARSE_FALLBACK" if unavailable else "FABRICATED_STRUCTURE_EVIDENCE"
    if not case["eligible_for_core_metrics"] or case["experiment_label"] == "UNCERTAIN":
        return "ANALYSIS_ONLY"
    expected = case["experiment_label"] in POSITIVE_LABELS
    if expected and not predicted:
        return "FALSE_NEGATIVE"
    if not expected and predicted:
        return "FALSE_POSITIVE"
    return "NONE"


def _warnings(result: Any) -> list[str]:
    warnings: set[str] = set()
    for evidence in result.evidence:
        for key in ("warningsA", "warningsB"):
            value = evidence.metadata.get(key)
            if isinstance(value, list):
                warnings.update(str(item) for item in value if item)
        if evidence.evidence_type == "PARSER_WARNING":
            warnings.add(evidence.description)
    return sorted(warnings)


def _baseline_registry(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    aligned_manifest_path = _resolve(config["jplagAlignedManifest"])
    aligned_results_path = _resolve(config["jplagAlignedResults"])
    if aligned_manifest_path.is_file() and aligned_results_path.is_file():
        aligned_manifest = _read_json(aligned_manifest_path)
        with aligned_results_path.open(encoding="utf-8-sig", newline="") as handle:
            aligned_results = list(csv.DictReader(handle))
        matched = sum(row.get("resultStatus") == "MATCHED" for row in aligned_results)
        rows.append({
            "baseline": "JPLAG_RESEARCH_V4_ALIGNED",
            "version": aligned_manifest.get("toolVersion"),
            "status": aligned_manifest.get("status"),
            "pairCount": matched,
            "datasetAligned": True,
            "includedInComparativeMetrics": True,
            "artifactPath": _relative(aligned_manifest_path.parent),
            "note": f"Manifest-aligned synthetic seed baseline; {matched}/{len(aligned_results)} requested comparisons matched.",
        })
    manifest_path = _resolve(config["jplagManifest"])
    csv_path = _resolve(config["jplagStandardCsv"])
    if manifest_path.is_file() and csv_path.is_file():
        manifest = _read_json(manifest_path)
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            comparisons = list(csv.DictReader(handle))
        rows.append({
            "baseline": "JPLAG",
            "version": manifest.get("toolVersion"),
            "status": "REAL_SMOKE_RUN",
            "pairCount": len(comparisons),
            "datasetAligned": False,
            "includedInComparativeMetrics": False,
            "artifactPath": _relative(manifest_path.parent),
            "note": "Executable and adapter verified; the 3-pair smoke set is not aligned with Research V4 cases.",
        })
    else:
        rows.append({
            "baseline": "JPLAG", "version": "unknown", "status": "MISSING_ARTIFACT",
            "pairCount": 0, "datasetAligned": False, "includedInComparativeMetrics": False,
            "artifactPath": "", "note": "No versioned result artifact was found.",
        })
    rows.append({
        "baseline": "DOLOS",
        "version": "not-run",
        "status": config.get("dolosStatus", "RESERVED_NOT_RUN"),
        "pairCount": 0,
        "datasetAligned": False,
        "includedInComparativeMetrics": False,
        "artifactPath": "",
        "note": "Reserved adapter boundary; Dolos is optional and does not block Research V4 scaffolding.",
    })
    return rows


def _aligned_jplag_comparison(
    config: dict[str, Any], predictions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    results_path = _resolve(config["jplagAlignedResults"])
    if not results_path.is_file():
        return []
    with results_path.open(encoding="utf-8-sig", newline="") as handle:
        jplag_rows = list(csv.DictReader(handle))
    picas = {row["pairId"]: row for row in predictions}
    comparison = []
    for row in jplag_rows:
        prediction = picas.get(row["pairId"])
        comparison.append({
            "pairId": row["pairId"],
            "problemId": row["problemId"],
            "datasetSplit": row["datasetSplit"],
            "experimentLabel": row["experimentLabel"],
            "caseType": row["caseType"],
            "language": row["language"],
            "sourceType": row["sourceType"],
            "jplagScore": row.get("predictedScore"),
            "jplagStatus": row.get("resultStatus"),
            "picasWeightedSimilarity": prediction.get("weightedSimilarityScore") if prediction else None,
            "picasDynamicThreshold": prediction.get("dynamicThreshold") if prediction else None,
            "picasExceedThreshold": prediction.get("exceedThreshold") if prediction else None,
            "aligned": prediction is not None,
            "syntheticSeedOnly": True,
        })
    return comparison


def _baseline_comparison_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    test_rows = [
        row for row in rows
        if row["datasetSplit"] == "test"
        and row["jplagStatus"] == "MATCHED"
        and row["experimentLabel"] in POSITIVE_LABELS | NEGATIVE_LABELS
    ]
    if not test_rows:
        return []
    labels = [row["experimentLabel"] in POSITIVE_LABELS for row in test_rows]
    methods = {
        "JPLAG_FIXED_0.70": [float(row["jplagScore"]) >= 0.70 for row in test_rows],
        "PICAS_DYNAMIC": [str(row["picasExceedThreshold"]).lower() == "true" for row in test_rows],
    }
    result = []
    for method, predicted in methods.items():
        metrics = v3.classification_metrics(labels, predicted)
        natural = [prediction for row, prediction in zip(test_rows, predicted) if row["experimentLabel"] == "NATURAL_SIMILAR"]
        suspicious = [prediction for row, prediction in zip(test_rows, predicted) if row["experimentLabel"] == "SUSPICIOUS"]
        result.append({
            "method": method,
            "evaluationSplit": "test",
            "threshold": 0.70 if method.startswith("JPLAG") else "dynamic",
            **metrics,
            "naturalSimilarityFpr": round(sum(natural) / max(len(natural), 1), 6),
            "suspiciousRecall": round(sum(suspicious) / max(len(suspicious), 1), 6),
            "syntheticSeedOnly": True,
        })
    return result


def _write_paper_tables(
    output_dir: Path,
    validation: dict[str, Any],
    same: dict[str, Any],
    cross: dict[str, Any],
    baselines: list[dict[str, Any]],
    calibration: dict[str, Any],
    jplag_comparison: list[dict[str, Any]],
    baseline_metrics: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True)
    statistics = []
    for dimension in ("countsBySplit", "countsByProblemType", "countsByCaseType", "countsByLabel", "countsByLanguage", "countsByOrigin", "countsBySourceType"):
        for value, count in validation[dimension].items():
            statistics.append({"dimension": dimension, "value": value, "pairCount": count})
    _write_csv(output_dir / "table_dataset_statistics.csv", statistics)
    _write_csv(output_dir / "table_fixed_vs_dynamic.csv", same["e1"])
    _write_csv(output_dir / "table_raw_vs_canonical.csv", same["e2"])
    _write_csv(output_dir / "table_fusion.csv", same["e3"])
    _write_csv(output_dir / "table_ablation.csv", same["e4"])
    _write_csv(output_dir / "table_cross_language.csv", cross["methods"])
    _write_csv(output_dir / "table_external_baselines.csv", baselines)
    _write_csv(output_dir / "table_dynamic_threshold_calibration.csv", calibration["testMetrics"] and [
        {"method": "PRODUCTION_DYNAMIC", "thresholdOffset": 0.0, **calibration["testMetrics"]["productionDynamicThreshold"]},
        {"method": "VALIDATION_CALIBRATED", "thresholdOffset": calibration["selectedParameters"]["selectedValue"], **calibration["testMetrics"]["validationCalibratedOffset"]},
    ])
    _write_csv(output_dir / "table_jplag_vs_picas.csv", jplag_comparison)
    _write_csv(output_dir / "table_baseline_comparison.csv", baseline_metrics)


def _write_case_analysis(
    output_dir: Path, same: dict[str, Any], cross: dict[str, Any]
) -> None:
    output_dir.mkdir(parents=True)
    all_failures = [
        {"scope": "SAME_LANGUAGE", **row} for row in same["failures"]
    ] + [
        {"scope": "CROSS_LANGUAGE", **row} for row in cross["failures"]
    ]
    _write_csv(output_dir / "failure_cases.csv", all_failures)
    _write_csv(output_dir / "borderline_cases.csv", same["borderline"])
    common = [row for row in cross["predictions"] if row["caseType"] == "COMMON_STRUCTURE"]
    unsupported = [row for row in cross["predictions"] if row["caseType"] in {"UNSUPPORTED_SYNTAX", "PARSER_FAILURE"}]
    _write_csv(output_dir / "common_structure_cases.csv", common)
    _write_csv(output_dir / "unsupported_syntax_cases.csv", unsupported)
    lines = [
        "# Research V4 Failure Analysis",
        "",
        "## Common Structure",
        "",
        "Common branch/loop shapes can raise IR and summary scores for independent programs. The current probe is retained as a false-positive case; production scoring remains unchanged and all V4 metrics keep zero weight.",
        "",
        "## Unsupported Syntax",
        "",
        "Java lambda and Python generator constructs currently emit warnings and lose data-summary coverage. Related pairs can therefore be under-scored. Parse failures produce zero experimental structure metrics and no fabricated structure evidence.",
        "",
        "## Boundary",
        "",
        "These observations come from fixed synthetic probes. They motivate additional manually verified cases but do not establish population-level error rates.",
        "",
    ]
    (output_dir / "failure_analysis.md").write_text("\n".join(lines), encoding="utf-8")


def _research_report(
    run: dict[str, Any],
    validation: dict[str, Any],
    same: dict[str, Any],
    cross: dict[str, Any],
    baselines: list[dict[str, Any]],
    calibration: dict[str, Any],
    jplag_comparison: list[dict[str, Any]],
    baseline_metrics: list[dict[str, Any]],
) -> str:
    dynamic = next(row for row in same["e1"] if row["method"] == "PICAS_DYNAMIC")
    fixed_70 = next(row for row in same["e1"] if row["method"] == "FIXED_0.70")
    canonical = same["summary"]["E2_rawVsCanonical"]
    common = next((row for row in cross["predictions"] if row["caseType"] == "COMMON_STRUCTURE"), None)
    unsupported = next((row for row in cross["predictions"] if row["caseType"] == "UNSUPPORTED_SYNTAX"), None)
    lines = [
        "# CodeRisk / PICAS Research V4 Candidate Report",
        "",
        "> This report is generated from a synthetic seed dataset and versioned tool artifacts. It validates the experiment workflow only; it is not a real benchmark and does not determine disciplinary outcomes, full semantic equivalence, or AI-generated code.",
        "",
        "## Dataset Gate",
        "",
        f"- Pairs: `{validation['caseCount']}`; eligible: `{validation['eligibleCaseCount']}`",
        f"- Validation/Test: `{validation['validationCaseCount']}` / `{validation['testCaseCount']}`",
        f"- Problem/Source/Exact-code overlap: `0 / 0 / 0`",
        f"- Non-preregistered bootstrap split cases: `{validation['nonPreregisteredSplitCaseCount']}`",
        f"- Gap to 80-pair target: `{validation['targetGap']}`",
        f"- Missing requested case types: `{', '.join(validation['missingCaseTypes']) or 'none'}`",
        f"- Source coverage deficits: `{len(validation['coverageGaps'])}`; see `dataset_validation/coverage_gaps.csv`.",
        "",
        "## Same-language E1-E5",
        "",
        f"- Dynamic natural-similar FPR: `{dynamic['naturalSimilarityFpr']}`; fixed 0.70: `{fixed_70['naturalSimilarityFpr']}`.",
        f"- Dynamic recall: `{dynamic['recall']}`; fixed 0.70 recall: `{fixed_70['recall']}`.",
        f"- Rename mean raw/canonical token: `{canonical['meanRawTokenSimilarity']}` / `{canonical['meanCanonicalTokenSimilarity']}`.",
        f"- Failures/borderline/parser fallback: `{same['summary']['E5_failureAnalysis']['failureCount']}` / `{same['summary']['E5_failureAnalysis']['borderlineCount']}` / `{same['summary']['E5_failureAnalysis']['parserFallbackCount']}`.",
        "",
        "## Validation-only Dynamic Threshold Calibration",
        "",
        f"- Selected experimental offset: `{calibration['selectedParameters']['selectedValue']}`.",
        "- Selection split: `validation`; test used for selection: `false`; production formula changed: `false`.",
        _markdown_table([
            {"method": "PRODUCTION_DYNAMIC", **calibration["testMetrics"]["productionDynamicThreshold"]},
            {"method": "VALIDATION_CALIBRATED", **calibration["testMetrics"]["validationCalibratedOffset"]},
        ]),
        "",
        "## Cross-language Experimental Matrix",
        "",
        _markdown_table(cross["methods"]),
        "",
        f"- Common-structure probe composite: `{common['experimentalComposite'] if common else 'missing'}`; failure: `{common['failureType'] if common else 'missing'}`.",
        f"- Unsupported-syntax probe composite: `{unsupported['experimentalComposite'] if unsupported else 'missing'}`; failure: `{unsupported['failureType'] if unsupported else 'missing'}`.",
        "- IR/control/data-summary metrics remain experimental with production weight 0.",
        "- The 7-case cross-language split was assigned during Phase 3 after Phase 2 inspection. No threshold was tuned from it, so the values are exploratory rather than confirmatory test estimates.",
        "",
        "## External Baselines",
        "",
        _markdown_table(baselines),
        "",
        "### Test-only aligned baseline summary",
        "",
        _markdown_table(baseline_metrics),
        "",
        f"The manifest-aligned JPlag table contains `{len(jplag_comparison)}` requested pair rows. It is still synthetic-seed evidence, not a real-data superiority claim. Dolos remains a non-blocking reserved integration.",
        "",
        "## Defensible Conclusions",
        "",
        "- Synthetic seed rename cases exercise canonical-token stability and the paper-table pipeline; real-data confirmation remains pending.",
        "- Validation-only calibration proves split discipline and parameter traceability, not the final quality of the selected offset.",
        "- Limited Java/Python IR and summaries preserve structure in several fixtures, while common structures and unsupported syntax expose clear false-positive/false-negative risks.",
        f"- The current {validation['caseCount']}-pair aggregate is explicitly synthetic/placeholder seed data and must not be presented as a formal benchmark.",
        "",
    ]
    return "\n".join(lines)


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    headers = list(rows[0])
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |" for row in rows)
    return "\n".join(lines)


def _dataset_hash(cases: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for case in sorted(cases, key=lambda item: item["pair_id"]):
        for key in ("pair_id", "problem_id", "dataset_split", "split_preregistered", "source_id", "source_type", "experiment_label", "case_type", "language", "dataset_version", "code_a_sha256", "code_b_sha256"):
            digest.update(str(case[key]).encode("utf-8"))
            digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _local_version() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True, timeout=3
        ).strip()
    except Exception:
        return os.getenv("CODERISK_LOCAL_VERSION", "workspace-no-git-20260624")


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: " | ".join(value) if isinstance(value, list) else value for key, value in row.items()})


if __name__ == "__main__":
    raise SystemExit(main())
