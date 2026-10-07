from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


POSITIVE_LABELS = {"SIMILAR", "SUSPICIOUS", "TRANSFORMED"}
NEGATIVE_LABELS = {"INDEPENDENT", "NATURAL_SIMILAR"}
VALID_LABELS = POSITIVE_LABELS | NEGATIVE_LABELS | {"UNCERTAIN"}
VALID_CASE_TYPES = {
    "ORIGINAL_COPY",
    "HUMAN_REWRITE",
    "VARIABLE_RENAME",
    "PARAMETER_RENAME",
    "FUNCTION_RENAME",
    "FORMAT_COMMENT_CHANGE",
    "LOCAL_REORDER",
    "SPLIT_MERGE",
    "CROSSLANG_REWRITE",
    "AI_REWRITE",
    "COMMON_STRUCTURE",
    "UNSUPPORTED_SYNTAX",
    "PARSER_FAILURE",
    "NATURAL_TEMPLATE",
    "INDEPENDENT_SOLUTION",
}
VALID_LANGUAGES = {"java", "python", "c"}
VALID_SPLITS = {"validation", "test"}
VALID_DATA_ORIGINS = {"SYNTHETIC", "MANUAL", "PUBLIC", "HISTORICAL_AUTHORIZED"}
VALID_SOURCE_TYPES = {"manual", "synthetic", "ai_assisted", "external", "placeholder"}
MANUAL_REQUIRED_FIELDS = {
    "pair_id",
    "problem_id",
    "problem_type",
    "problem_group",
    "dataset_split",
    "split_preregistered",
    "source_id",
    "experiment_label",
    "case_type",
    "language",
    "language_a",
    "language_b",
    "dataset_version",
    "data_origin",
    "source_type",
    "synthetic",
    "eligible_for_core_metrics",
    "question",
    "code_a_path",
    "code_b_path",
    "provenance",
}


class DatasetValidationError(ValueError):
    def __init__(self, report: dict[str, Any]) -> None:
        self.report = report
        super().__init__("; ".join(report["errors"]))


def load_research_dataset(
    manifest_path: Path,
    *,
    raise_on_error: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    manifest_path = manifest_path.resolve()
    manifest = _read_json(manifest_path)
    cases: list[dict[str, Any]] = []
    load_errors: list[str] = []
    source_counts: dict[str, int] = {}

    for source in manifest.get("sources", []):
        if not source.get("include", True):
            continue
        source_id = str(source.get("id", "missing-source-id"))
        try:
            source_path = _resolve_source_path(manifest_path.parent, source["path"])
            payload = _read_json(source_path)
            source_cases = [_finalize_case(case) for case in _load_source(source, source_path, payload, manifest)]
            source_counts[source_id] = len(source_cases)
            cases.extend(source_cases)
        except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
            load_errors.append(f"Source {source_id} could not be loaded: {error}")

    report = validate_cases(manifest, cases, source_counts=source_counts, initial_errors=load_errors)
    if raise_on_error and not report["valid"]:
        raise DatasetValidationError(report)
    return manifest, cases, report


def validate_cases(
    manifest: dict[str, Any],
    cases: list[dict[str, Any]],
    *,
    source_counts: dict[str, int] | None = None,
    initial_errors: list[str] | None = None,
) -> dict[str, Any]:
    errors = list(initial_errors or [])
    warnings: list[str] = []
    seen_pair_ids: set[str] = set()
    problems_by_split: dict[str, set[str]] = defaultdict(set)
    sources_by_split: dict[str, set[str]] = defaultdict(set)
    code_hash_splits: dict[str, set[str]] = defaultdict(set)
    code_hash_cases: dict[str, set[str]] = defaultdict(set)
    families_by_split: dict[str, set[str]] = defaultdict(set)

    for case in cases:
        case_id = str(case.get("pair_id", case.get("case_id", "<missing>")))
        missing = sorted(field for field in _normalized_required_fields() if field not in case)
        if missing:
            errors.append(f"Case {case_id} is missing normalized fields: {missing}")
            continue
        if case_id in seen_pair_ids:
            errors.append(f"Duplicate pair_id: {case_id}")
        seen_pair_ids.add(case_id)
        if case["pair_id"] != case["case_id"]:
            errors.append(f"Case {case_id} compatibility case_id must equal pair_id")
        if case["dataset_split"] != case["split"]:
            errors.append(f"Case {case_id} compatibility split must equal dataset_split")

        split = case["split"]
        if split not in VALID_SPLITS:
            errors.append(f"Case {case_id} has unsupported split: {split}")
        else:
            problems_by_split[split].add(case["problem_id"])
            sources_by_split[split].add(case["source_id"])
            families = case.get('source_family_ids', [])
            if not isinstance(families, list) or any(not isinstance(x, str) or not x.strip() for x in families):
                errors.append(f'Case {case_id} has invalid source_family_ids')
            else:
                families_by_split[split].update(families)
        if not isinstance(case["split_preregistered"], bool):
            errors.append(f"Case {case_id} split_preregistered must be boolean")

        if case["experiment_label"] not in VALID_LABELS:
            errors.append(f"Case {case_id} has unknown experiment_label: {case['experiment_label']}")
        if case["case_type"] not in VALID_CASE_TYPES:
            errors.append(f"Case {case_id} has unknown case_type: {case['case_type']}")
        if case["language_a"] not in VALID_LANGUAGES or case["language_b"] not in VALID_LANGUAGES:
            errors.append(f"Case {case_id} has unsupported language pair")
        expected_language = f"{case['language_a']}-{case['language_b']}"
        if case["language"] != expected_language and not (
            case["language_a"] == case["language_b"] and case["language"] == case["language_a"]
        ):
            errors.append(
                f"Case {case_id} language must be {expected_language} or the same-language shorthand"
            )
        if case["data_origin"] not in VALID_DATA_ORIGINS:
            errors.append(f"Case {case_id} has unknown data_origin: {case['data_origin']}")
        if case["source_type"] not in VALID_SOURCE_TYPES:
            errors.append(f"Case {case_id} has unknown source_type: {case['source_type']}")
        if case["source_type"] in {"synthetic", "placeholder"} and not case["synthetic"]:
            errors.append(f"Case {case_id} source_type={case['source_type']} must be marked synthetic")
        if not isinstance(case["synthetic"], bool) or not isinstance(case["eligible_for_core_metrics"], bool):
            errors.append(f"Case {case_id} synthetic/eligible flags must be boolean")
        if case["experiment_label"] == "UNCERTAIN" and case["eligible_for_core_metrics"]:
            errors.append(f"Case {case_id} is UNCERTAIN and cannot enter core metrics")
        if not _valid_question(case["question"]):
            errors.append(f"Case {case_id} has incomplete question metadata")
        if not case["code_a"].strip() or not case["code_b"].strip():
            errors.append(f"Case {case_id} contains empty code")
        if case.get("hash_mismatches"):
            errors.append(f"Case {case_id} declares code hashes that do not match the loaded files")
        _validate_provenance(case, errors, warnings)

        if split in VALID_SPLITS:
            for code, declared_digest in (
                (case["code_a"], case["code_a_sha256"]),
                (case["code_b"], case["code_b_sha256"]),
            ):
                digest = _sha256_text(code)
                if digest != declared_digest:
                    errors.append(f"Case {case_id} declared code hash does not match loaded content")
                code_hash_splits[digest].add(split)
                code_hash_cases[digest].add(case_id)

    problem_overlap = sorted(problems_by_split["validation"] & problems_by_split["test"])
    source_overlap = sorted(sources_by_split["validation"] & sources_by_split["test"])
    code_overlap = sorted(
        {case_id for digest, splits in code_hash_splits.items() if len(splits) > 1 for case_id in code_hash_cases[digest]}
    )
    if problem_overlap:
        errors.append(f"Problem leakage across validation/test: {problem_overlap}")
    if source_overlap:
        errors.append(f"Source leakage across validation/test: {source_overlap}")
    family_overlap = sorted(families_by_split['validation'] & families_by_split['test'])
    if family_overlap:
        errors.append(f'Source-family leakage across validation/test: {family_overlap}')
    if code_overlap:
        errors.append(f"Exact code content leakage across validation/test: {code_overlap}")

    target = manifest.get("target_pair_count", {})
    target_min = int(target.get("minimum", 0))
    target_max = int(target.get("maximum", 0))
    target_gap = max(target_min - len(cases), 0)
    if target_gap:
        warnings.append(f"Dataset is below the research target by {target_gap} pairs")
    if target_max and len(cases) > target_max:
        warnings.append(f"Dataset exceeds the advisory maximum by {len(cases) - target_max} pairs")

    non_preregistered_split_cases = sorted(
        case["case_id"] for case in cases if not case["split_preregistered"]
    )
    if non_preregistered_split_cases:
        warnings.append(
            f"{len(non_preregistered_split_cases)} cases use a non-preregistered bootstrap split and cannot support confirmatory claims"
        )

    required_problem_types = set(manifest.get("required_problem_types", []))
    required_case_types = set(manifest.get("required_case_types", []))
    present_problem_types = {case["problem_type"] for case in cases}
    present_case_types = {case["case_type"] for case in cases}
    missing_problem_types = sorted(required_problem_types - present_problem_types)
    missing_case_types = sorted(required_case_types - present_case_types)
    if missing_problem_types:
        warnings.append(f"Missing requested problem types: {missing_problem_types}")
    if missing_case_types:
        warnings.append(f"Missing requested case types: {missing_case_types}")

    coverage_gaps = _coverage_gaps(manifest, cases)
    if coverage_gaps:
        warnings.append(f"Dataset has {len(coverage_gaps)} declared coverage deficits")

    report = {
        "valid": not errors,
        "datasetId": manifest.get("dataset_id"),
        "datasetVersion": manifest.get("dataset_version"),
        "datasetStatus": manifest.get("status"),
        "caseCount": len(cases),
        "eligibleCaseCount": sum(bool(case["eligible_for_core_metrics"]) for case in cases),
        "validationCaseCount": sum(case["split"] == "validation" for case in cases),
        "testCaseCount": sum(case["split"] == "test" for case in cases),
        "validationProblemCount": len(problems_by_split["validation"]),
        "testProblemCount": len(problems_by_split["test"]),
        "targetMinimum": target_min,
        "targetMaximum": target_max,
        "targetGap": target_gap,
        "problemOverlap": problem_overlap,
        "sourceOverlap": source_overlap,
        "sourceFamilyOverlap": family_overlap,
        "exactCodeOverlapCases": code_overlap,
        "nonPreregisteredSplitCaseCount": len(non_preregistered_split_cases),
        "nonPreregisteredSplitCases": non_preregistered_split_cases,
        "missingProblemTypes": missing_problem_types,
        "missingCaseTypes": missing_case_types,
        "coverageGaps": coverage_gaps,
        "countsBySplit": _counter(cases, "split"),
        "countsByProblemType": _counter(cases, "problem_type"),
        "countsByCaseType": _counter(cases, "case_type"),
        "countsByLabel": _counter(cases, "experiment_label"),
        "countsByLanguage": _counter(cases, "language"),
        "countsByOrigin": _counter(cases, "data_origin"),
        "countsBySourceType": _counter(cases, "source_type"),
        "sourceCounts": source_counts or {},
        "errors": errors,
        "warnings": warnings,
    }
    return report


def write_validation_artifacts(
    output_dir: Path,
    manifest: dict[str, Any],
    cases: list[dict[str, Any]],
    report: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "validation_report.json", report)
    _write_json(output_dir / "normalized_manifest.json", {
        "datasetId": manifest.get("dataset_id"),
        "datasetVersion": manifest.get("dataset_version"),
        "caseCount": len(cases),
        "cases": [_case_index_row(case) for case in cases],
    })
    _write_csv(output_dir / "case_index.csv", [_case_index_row(case) for case in cases])
    _write_csv(output_dir / "dataset_statistics.csv", _statistics_rows(report))
    _write_csv(output_dir / "coverage_gaps.csv", report["coverageGaps"])
    (output_dir / "validation_report.md").write_text(_validation_markdown(report), encoding="utf-8")


def _load_source(
    source: dict[str, Any],
    source_path: Path,
    payload: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    source_format = source["format"]
    if source_format == "PICAS_V3_INLINE_JSON":
        return [_normalize_v3_case(case, source, payload) for case in payload.get("cases", [])]
    if source_format == "PICAS_V4_CROSSLANG_JSON":
        return [_normalize_v4_case(case, source, source_path, payload) for case in payload.get("cases", [])]
    if source_format == "RESEARCH_V4_PAIRS_JSON":
        return [
            _normalize_manual_case(case, source, source_path, payload, manifest)
            for case in payload.get("cases", [])
        ]
    raise ValueError(f"Unsupported source format: {source_format}")


def _normalize_v3_case(
    case: dict[str, Any], source: dict[str, Any], payload: dict[str, Any]
) -> dict[str, Any]:
    language = str(case["language"]).lower()
    return {
        **case,
        "pair_id": case["case_id"],
        "dataset_split": case["split"],
        "split_preregistered": True,
        "language_a": language,
        "language_b": language,
        "data_origin": source["data_origin"],
        "source_type": "synthetic",
        "synthetic": True,
        "eligible_for_core_metrics": case["experiment_label"] != "UNCERTAIN",
        "source_dataset": source["id"],
        "source_dataset_version": payload["dataset_version"],
        "provenance": {"source": "existing synthetic V3 shard"},
        "notes": "Imported from the fixed V4-ready synthetic shard.",
    }


def _normalize_v4_case(
    case: dict[str, Any],
    source: dict[str, Any],
    source_path: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    root = source_path.parent
    problem_type = case["problemType"]
    return {
        "case_id": case["caseId"],
        "pair_id": case["caseId"],
        "problem_id": case["problemId"],
        "problem_type": problem_type,
        "problem_group": case["problemGroup"],
        "split": case["split"],
        "dataset_split": case["split"],
        "split_preregistered": bool(payload.get("splitPreregistered", False)),
        "source_id": case["sourceId"],
        "experiment_label": case["experimentLabel"],
        "case_type": case["caseType"],
        "language": case["language"],
        "language_a": case["languageA"],
        "language_b": case["languageB"],
        "dataset_version": case["datasetVersion"],
        "data_origin": case["dataOrigin"],
        "source_type": "synthetic",
        "synthetic": case["synthetic"],
        "eligible_for_core_metrics": case["eligibleForCoreMetrics"],
        "question": {
            "title": f"Experimental {problem_type.replace('_', ' ')} case",
            "description": "Fixed synthetic Java/Python pair for limited Research V4 structure analysis.",
            "input_format": "See source fixture.",
            "output_format": "See source fixture.",
            "constraints_text": "Experimental fixture only.",
        },
        "code_a": _read_code(root, case["javaPath"]),
        "code_b": _read_code(root, case["pythonPath"]),
        "source_dataset": source["id"],
        "source_dataset_version": payload["datasetVersion"],
        "provenance": {"source": "existing synthetic V4 Phase 2 shard"},
        "notes": case.get("notes", "Fixed cross-language prototype case."),
    }


def _normalize_manual_case(
    case: dict[str, Any],
    source: dict[str, Any],
    source_path: Path,
    payload: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    missing = sorted(MANUAL_REQUIRED_FIELDS - set(case))
    if missing:
        raise ValueError(f"Manual case {case.get('case_id', '<missing>')} is missing fields: {missing}")
    if case["dataset_version"] != payload.get("dataset_version"):
        raise ValueError(f"Manual case dataset version mismatch: {case['pair_id']}")
    if payload.get("dataset_version") != manifest.get("dataset_version"):
        raise ValueError("Manual shard version must match the Research V4 manifest")
    dataset_root = _find_dataset_root(source_path)
    code_a_path = _safe_dataset_path(dataset_root, case["code_a_path"])
    code_b_path = _safe_dataset_path(dataset_root, case["code_b_path"])
    return {
        **case,
        "case_id": case["pair_id"],
        "split": case["dataset_split"],
        "code_a": code_a_path.read_text(encoding="utf-8"),
        "code_b": code_b_path.read_text(encoding="utf-8"),
        "source_dataset": source["id"],
        "source_dataset_version": payload["dataset_version"],
        "notes": case.get("notes", ""),
    }


def _validate_provenance(
    case: dict[str, Any], errors: list[str], warnings: list[str]
) -> None:
    case_id = case["case_id"]
    provenance = case.get("provenance")
    if not isinstance(provenance, dict) or not provenance:
        errors.append(f"Case {case_id} is missing provenance")
        return
    if case["case_type"] == "AI_REWRITE":
        required = {"model_name", "prompt_template", "generation_time", "manual_check_status", "functional_check_status"}
        missing = sorted(required - set(provenance))
        if missing and case["eligible_for_core_metrics"]:
            errors.append(f"Eligible AI_REWRITE case {case_id} lacks provenance fields: {missing}")
        if provenance.get("manual_check_status") != "VERIFIED" or provenance.get("functional_check_status") != "PASSED":
            if case["eligible_for_core_metrics"]:
                errors.append(f"Eligible AI_REWRITE case {case_id} is not manually and functionally verified")
            else:
                warnings.append(f"AI_REWRITE case {case_id} is retained for analysis only")
    if case["data_origin"] != "SYNTHETIC" and not provenance.get("license_or_authorization"):
        errors.append(f"Non-synthetic case {case_id} lacks license_or_authorization")


def _normalized_required_fields() -> set[str]:
    return {
        "pair_id", "case_id", "problem_id", "problem_type", "problem_group", "dataset_split", "split", "split_preregistered", "source_id",
        "experiment_label", "case_type", "language", "language_a", "language_b",
        "dataset_version", "data_origin", "source_type", "synthetic", "eligible_for_core_metrics",
        "question", "code_a", "code_b", "code_a_sha256", "code_b_sha256", "source_dataset", "provenance",
    }


def _valid_question(question: Any) -> bool:
    return isinstance(question, dict) and bool(question.get("title")) and bool(question.get("description"))


def _counter(cases: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(case[key]) for case in cases).items()))


def _case_index_row(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "pairId": case["pair_id"],
        "caseId": case["case_id"],
        "problemId": case["problem_id"],
        "problemType": case["problem_type"],
        "problemGroup": case["problem_group"],
        "datasetSplit": case["dataset_split"],
        "split": case["split"],
        "splitPreregistered": case["split_preregistered"],
        "sourceId": case["source_id"],
        "experimentLabel": case["experiment_label"],
        "caseType": case["case_type"],
        "language": case["language"],
        "datasetVersion": case["dataset_version"],
        "dataOrigin": case["data_origin"],
        "sourceType": case["source_type"],
        "codeASha256": case["code_a_sha256"],
        "codeBSha256": case["code_b_sha256"],
        "synthetic": case["synthetic"],
        "eligibleForCoreMetrics": case["eligible_for_core_metrics"],
        "sourceDataset": case["source_dataset"],
    }


def _statistics_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in ("countsBySplit", "countsByProblemType", "countsByCaseType", "countsByLabel", "countsByLanguage", "countsByOrigin", "countsBySourceType"):
        for value, count in report[group].items():
            rows.append({"dimension": group, "value": value, "pairCount": count})
    return rows


def _validation_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Research V4 Dataset Validation",
        "",
        f"- Valid: `{str(report['valid']).lower()}`",
        f"- Dataset: `{report['datasetVersion']}`",
        f"- Pairs: `{report['caseCount']}` (eligible: `{report['eligibleCaseCount']}`)",
        f"- Validation/Test: `{report['validationCaseCount']}` / `{report['testCaseCount']}`",
        f"- Problem overlap: `{len(report['problemOverlap'])}`",
        f"- Source overlap: `{len(report['sourceOverlap'])}`",
        f"- Exact-code overlap cases: `{len(report['exactCodeOverlapCases'])}`",
        f"- Non-preregistered split cases: `{report['nonPreregisteredSplitCaseCount']}`",
        f"- Target gap: `{report['targetGap']}`",
        f"- Declared coverage deficits: `{len(report['coverageGaps'])}`",
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {item}" for item in report["errors"] or ["None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in report["warnings"] or ["None"])
    lines.extend([
        "",
        "> Passing validation proves metadata and split isolation, not dataset representativeness or benchmark scale.",
        "",
    ])
    return "\n".join(lines)


def _resolve_source_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_file():
        raise ValueError(f"Source file does not exist: {path}")
    return path


def _safe_dataset_path(dataset_root: Path, value: str) -> Path:
    path = (dataset_root / value).resolve()
    if not path.is_relative_to(dataset_root.resolve()):
        raise ValueError(f"Manual code path escapes the dataset root: {value}")
    if not path.is_file():
        raise ValueError(f"Manual code file does not exist: {value}")
    return path


def _find_dataset_root(source_path: Path) -> Path:
    for candidate in (source_path.parent, *source_path.parents):
        if (candidate / "dataset.json").is_file():
            return candidate
    raise ValueError(f"Could not locate dataset root for source: {source_path}")


def _read_code(root: Path, value: str) -> str:
    return (root / value).resolve().read_text(encoding="utf-8")


def _finalize_case(case: dict[str, Any]) -> dict[str, Any]:
    finalized = dict(case)
    finalized.setdefault("pair_id", finalized.get("case_id"))
    finalized.setdefault("case_id", finalized.get("pair_id"))
    finalized.setdefault("dataset_split", finalized.get("split"))
    finalized.setdefault("split", finalized.get("dataset_split"))
    finalized.setdefault("source_type", "synthetic" if finalized.get("synthetic") else "manual")
    actual_a = _sha256_text(finalized["code_a"])
    actual_b = _sha256_text(finalized["code_b"])
    mismatches = []
    if finalized.get("code_a_sha256") not in {None, "", actual_a}:
        mismatches.append("code_a_sha256")
    if finalized.get("code_b_sha256") not in {None, "", actual_b}:
        mismatches.append("code_b_sha256")
    finalized["hash_mismatches"] = mismatches
    finalized["code_a_sha256"] = actual_a
    finalized["code_b_sha256"] = actual_b
    return finalized


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _coverage_gaps(manifest: dict[str, Any], cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = {
        "problem_type": "problem_type",
        "case_type": "case_type",
        "experiment_label": "experiment_label",
        "source_type": "source_type",
    }
    gaps: list[dict[str, Any]] = []
    for dimension, requirements in manifest.get("minimum_counts", {}).items():
        field = fields.get(dimension)
        if not field or not isinstance(requirements, dict):
            continue
        counts = Counter(str(case[field]) for case in cases)
        for value, required in requirements.items():
            current = counts.get(str(value), 0)
            missing = max(int(required) - current, 0)
            if missing:
                gaps.append({
                    "dimension": dimension,
                    "value": value,
                    "required": int(required),
                    "current": current,
                    "missing": missing,
                })
    return gaps


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
