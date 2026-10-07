from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from research_v4_dataset import load_research_dataset


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "experiment/datasets/research-v4/dataset.json"
DEFAULT_JAR = ROOT / "data/tools/jplag/jplag-6.2.0-jar-with-dependencies.jar"
DEFAULT_JAVA = Path("D:/DevEnvManager/envs/jdks/temurin-21/bin/java.exe")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and optionally run a manifest-aligned Research V4 JPlag baseline.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--jplag-jar", type=Path, default=DEFAULT_JAR)
    parser.add_argument("--java", type=Path, default=DEFAULT_JAVA)
    parser.add_argument("--tool-version", default="6.2.0")
    parser.add_argument("--min-tokens", type=int, default=5)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--picas-predictions", type=Path)
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"JPlag alignment output must be empty or new: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    prepared = prepare_inputs(args.manifest.resolve(), output_dir)
    results: list[dict[str, Any]] = []
    run_records: list[dict[str, Any]] = []
    if args.execute:
        if not args.jplag_jar.is_file() or not args.java.is_file():
            raise FileNotFoundError("JPlag jar and Java executable are required for --execute")
        results, run_records = execute_jplag(
            output_dir,
            prepared["alignmentRows"],
            args.jplag_jar.resolve(),
            args.java.resolve(),
            args.tool_version,
            args.min_tokens,
        )
        _write_csv(output_dir / "baseline_results.csv", results)
        if args.picas_predictions:
            comparison = align_with_picas(results, args.picas_predictions.resolve())
            _write_csv(output_dir / "jplag_vs_picas.csv", comparison)
    manifest = {
        "tool": "JPLAG",
        "toolVersion": args.tool_version,
        "datasetVersion": prepared["datasetVersion"],
        "datasetPairCount": prepared["datasetPairCount"],
        "alignedPairCount": len(prepared["alignmentRows"]),
        "excludedPairCount": len(prepared["excludedRows"]),
        "resultPairCount": len(results),
        "execute": args.execute,
        "minTokens": args.min_tokens,
        "jarSha256": _file_hash(args.jplag_jar) if args.jplag_jar.is_file() else None,
        "datasetAligned": True,
        "runRecords": run_records,
        "status": "FINISHED" if args.execute else "PREPARED",
    }
    _write_json(output_dir / "run_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


def prepare_inputs(manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    manifest, cases, report = load_research_dataset(manifest_path)
    alignment_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    written: dict[tuple[str, str], str] = {}

    for case in cases:
        reason = _exclusion_reason(case)
        if reason:
            excluded_rows.append({
                "pairId": case["pair_id"],
                "problemId": case["problem_id"],
                "language": case["language"],
                "caseType": case["case_type"],
                "experimentLabel": case["experiment_label"],
                "reason": reason,
            })
            continue
        language = case["language_a"]
        submission_a = _submission_id(case["problem_id"], case["code_a_sha256"])
        submission_b = _submission_id(case["problem_id"], case["code_b_sha256"])
        _write_submission(output_dir, language, submission_a, case["code_a"], written)
        _write_submission(output_dir, language, submission_b, case["code_b"], written)
        alignment_rows.append({
            "pairId": case["pair_id"],
            "problemId": case["problem_id"],
            "datasetSplit": case["dataset_split"],
            "experimentLabel": case["experiment_label"],
            "caseType": case["case_type"],
            "language": language,
            "submissionA": submission_a,
            "submissionB": submission_b,
            "sourceType": case["source_type"],
            "synthetic": case["synthetic"],
        })

    _write_csv(output_dir / "alignment_manifest.csv", alignment_rows)
    _write_csv(output_dir / "excluded_pairs.csv", excluded_rows)
    _write_json(output_dir / "preparation_summary.json", {
        "datasetVersion": manifest["dataset_version"],
        "datasetPairCount": len(cases),
        "alignedPairCount": len(alignment_rows),
        "excludedPairCount": len(excluded_rows),
        "validationValid": report["valid"],
        "languages": sorted({row["language"] for row in alignment_rows}),
    })
    return {
        "datasetVersion": manifest["dataset_version"],
        "datasetPairCount": len(cases),
        "alignmentRows": alignment_rows,
        "excludedRows": excluded_rows,
    }


def execute_jplag(
    output_dir: Path,
    alignment_rows: list[dict[str, Any]],
    jar: Path,
    java: Path,
    version: str,
    min_tokens: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_language: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in alignment_rows:
        rows_by_language[row["language"]].append(row)
    results: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    for language, rows in sorted(rows_by_language.items()):
        input_root = output_dir / "input" / language
        native_root = output_dir / "native" / language
        native_root.mkdir(parents=True, exist_ok=True)
        result_base = native_root / "results"
        language_flag = "python3" if language == "python" else language
        command = [
            str(java), "-jar", str(jar), "-l", language_flag, "-M", "RUN",
            "--csv-export", "-r", str(result_base), "--overwrite", "-n", "-1",
            "-t", str(min_tokens), str(input_root),
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
        native_csv = native_root / "results" / "results.csv"
        runs.append({
            "language": language,
            "languageFlag": language_flag,
            "exitCode": completed.returncode,
            "inputSubmissionCount": len({r["submissionA"] for r in rows} | {r["submissionB"] for r in rows}),
            "nativeCsv": _relative(native_csv),
            "command": " ".join(command),
            "stderrTail": completed.stderr[-1000:],
        })
        if completed.returncode != 0 or not native_csv.is_file():
            continue
        scores = _native_scores(native_csv)
        for row in rows:
            key = frozenset((row["submissionA"], row["submissionB"]))
            score = scores.get(key)
            results.append({
                **row,
                "method": "JPLAG",
                "methodVersion": version,
                "predictedScore": score,
                "resultStatus": "MATCHED" if score is not None else "NO_NATIVE_COMPARISON",
                "reason": "" if score is not None else "JPlag did not emit this requested comparison, usually because parsing or minimum-token requirements excluded a submission.",
            })
    return results, runs


def align_with_picas(jplag_rows: list[dict[str, Any]], predictions_path: Path) -> list[dict[str, Any]]:
    with predictions_path.open(encoding="utf-8-sig", newline="") as handle:
        picas = {row.get("pairId") or row.get("caseId"): row for row in csv.DictReader(handle)}
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
            "jplagScore": row["predictedScore"],
            "jplagStatus": row["resultStatus"],
            "picasWeightedSimilarity": prediction.get("weightedSimilarityScore") if prediction else None,
            "picasDynamicThreshold": prediction.get("dynamicThreshold") if prediction else None,
            "picasExceedThreshold": prediction.get("exceedThreshold") if prediction else None,
            "aligned": prediction is not None,
        })
    return comparison


def _exclusion_reason(case: dict[str, Any]) -> str | None:
    if case["language_a"] != case["language_b"]:
        return "CROSS_LANGUAGE_PAIR"
    if case["language_a"] not in {"java", "python"}:
        return "LANGUAGE_NOT_ENABLED_FOR_RESEARCH_JPLAG"
    if case["source_type"] == "placeholder" or case["case_type"] == "AI_REWRITE":
        return "PLACEHOLDER_NOT_ELIGIBLE"
    if case["case_type"] in {"PARSER_FAILURE", "UNSUPPORTED_SYNTAX"}:
        return "PARSER_OR_UNSUPPORTED_SYNTAX_PROBE"
    if not case["eligible_for_core_metrics"]:
        return "NOT_ELIGIBLE_FOR_CORE_METRICS"
    return None


def _write_submission(
    output_dir: Path,
    language: str,
    submission_id: str,
    code: str,
    written: dict[tuple[str, str], str],
) -> None:
    key = (language, submission_id)
    if key in written:
        if written[key] != code:
            raise ValueError(f"Submission id collision: {submission_id}")
        return
    extension = "java" if language == "java" else "py"
    filename = "Main.java" if language == "java" else "main.py"
    target = output_dir / "input" / language / submission_id / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code, encoding="utf-8")
    written[key] = code


def _submission_id(problem_id: str, digest: str) -> str:
    safe_problem = "".join(character.lower() if character.isalnum() else "-" for character in problem_id).strip("-")
    return f"{safe_problem}--{digest.removeprefix('sha256:')[:16]}"


def _native_scores(path: Path) -> dict[frozenset[str], float]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        frozenset((str(row["submissionName1"]), str(row["submissionName2"]))): float(row["averageSimilarity"])
        for row in rows
    }


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
