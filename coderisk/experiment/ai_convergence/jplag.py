"""Current-corpus diagnostic JPlag adapter; reuse native execution and pair alignment."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_convergence.protocol import digest, write_json, require_private_output
from research_v4_dataset import load_research_dataset
from research_v4_jplag import execute_jplag, _write_submission, DEFAULT_JAR, DEFAULT_JAVA
from similarity_ablation import evaluate, method_score, parse_ast_nodes
from run_fair_evaluation import write_csv


def prepare(dataset, output, *, execute=False, jar=DEFAULT_JAR, java=DEFAULT_JAVA, min_tokens=5):
    _, cases, _ = load_research_dataset(dataset)
    require_private_output(any(not case["synthetic"] for case in cases), output)
    if type(min_tokens) is not int or min_tokens < 1:
        raise ValueError("Positive frozen minimum token count required")
    if execute and (not jar.is_file() or not java.is_file()):
        raise ValueError("Existing local Java and JPlag required; never automatically download")
    if execute:
        with zipfile.ZipFile(jar) as archive:
            # Manifest version keys are ASCII; local build metadata can use another encoding.
            attributes = archive.read("META-INF/MANIFEST.MF").decode("latin-1")
        version = next((line.split(':', 1)[1].strip() for line in attributes.splitlines() if line.startswith('Implementation-Version:')), None)
        if version != "6.2.0":
            raise ValueError("This frozen native adapter requires actual Implementation-Version 6.2.0")
    output.mkdir(parents=True, exist_ok=False)
    rows, excluded, written = [], [], {}
    index = {r["pair_id"]: r for r in json.loads((dataset.parent / "pair_index.json").read_text(encoding="utf-8"))}
    for case in cases:
        if not all(parse_ast_nodes(case['code_' + side], case['language_' + side]).parsed for side in ('a', 'b')):
            excluded.append({"pair_id": case["pair_id"], "reason": "PARSE_FAILED_RETAINED_IN_PICAS_DESCRIPTIVE_COHORT"})
            continue
        submissions = []
        for side in ("a", "b"):
            # Distinct sessions with identical code remain distinct native submissions.
            name = "S-" + digest(index[case["pair_id"]]["sample_" + side].encode())[:24]
            _write_submission(output, case["language_" + side], name, case["code_" + side], written)
            submissions.append(name)
        rows.append({"pairId": case["pair_id"], "problemId": case["problem_id"], "datasetSplit": case["split"],
            "language": case["language_a"], "submissionA": submissions[0], "submissionB": submissions[1],
            "codeASha256": case["code_a_sha256"], "codeBSha256": case["code_b_sha256"],
            "experimentLabel": case["experiment_label"], "synthetic": case["synthetic"]})
    results, records = execute_jplag(output, rows, jar, java, "6.2.0", min_tokens) if execute else ([], [])
    write_csv(output / "baseline_results.csv", results)
    write_csv(output / "alignment.csv", rows)
    write_csv(output / "excluded.csv", excluded)
    manifest = {"status": "NOT_RUN_PREPARED" if not execute else "FAILED" if any(r["exitCode"] != 0 for r in records) else "FINISHED",
        "dataset_manifest_sha256": digest(dataset.read_bytes()), "baseline_results_sha256": digest((output / "baseline_results.csv").read_bytes()),
        "jar_sha256": digest(jar.read_bytes()) if jar.is_file() else None, "tool_version": "6.2.0",
        "min_tokens": min_tokens, "requested_pairs": len(cases), "prepared_pairs": len(rows), "excluded_pairs": excluded,
        "run_records": records, "label_mode": "DESCRIPTIVE_NOT_FORMAL", "synthetic": any(c["synthetic"] for c in cases),
        "template_policy": "NO_BASE_CODE_REMOVAL: production PICAS also retains registered template tokens in score",
        "source_execution": False, "live_model_calls": 0}
    write_json(output / "manifest.json", manifest)
    return manifest


def validate_baseline(directory, dataset, rows, config, formal):
    from ai_convergence.analyze import unestimable_metrics
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    csv_path = directory / "baseline_results.csv"
    if (manifest.get("tool_version"), manifest.get("min_tokens")) != (config["jplag"]["toolVersion"], config["jplag"]["minTokens"]):
        raise ValueError("Native version/min-tokens do not match frozen comparison config")
    if not manifest.get("template_policy", '').startswith(config["jplag"]["templatePolicy"]):
        raise ValueError("Native template policy does not match frozen comparison config")
    if manifest["status"] != "FINISHED" or manifest["dataset_manifest_sha256"] != digest(dataset.read_bytes()) or manifest["baseline_results_sha256"] != digest(csv_path.read_bytes()):
        raise ValueError("JPlag is not completed or current dataset/score hash does not align")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        baseline = list(csv.DictReader(handle))
    by_pair, expected = {}, {r["pair_id"]: r for r in rows}
    for native in baseline:
        pair = native["pairId"]
        if pair in by_pair or pair not in expected:
            raise ValueError("Duplicate or unknown native pair")
        row = expected[pair]
        if native["codeASha256"] != row["code_a_sha256"] or native["codeBSha256"] != row["code_b_sha256"]:
            raise ValueError("JPlag current source hashes mismatch")
        by_pair[pair] = native
    matched = [r for r in rows if by_pair.get(r["pair_id"], {}).get("resultStatus") == "MATCHED" and
               all(method_score(r, m) is not None for m in config["methods"])]
    picas = evaluate(matched, config)
    external_method = {"name": "JPLAG_NATIVE", "scoreMode": "WEIGHTED", "weights": {"raw": 1.0}, "thresholdMode": "FIXED"}
    external = evaluate([{**r, "raw": float(by_pair[r["pair_id"]]["predictedScore"])} for r in matched], {**config, "methods": [external_method]})
    if not formal:
        unestimable_metrics(picas)
        unestimable_metrics(external)
    return {"status": "CURRENT_NATIVE_ALIGNED_DESCRIPTIVE" if not formal else "CURRENT_NATIVE_ALIGNED_FORMAL",
        "paired_common_count": len(matched), "paired_common_ids": [r["pair_id"] for r in matched],
        "requested_count": len(rows), "missing_not_zero": [r["pair_id"] for r in rows if r not in matched],
        "methods": picas["metrics"] + external["metrics"], "template_policy": manifest["template_policy"],
        "threshold_selection": "EACH_METHOD_VALIDATION_ONLY_SAME_COMMON_COHORT", "native_manifest": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--jar", type=Path, default=DEFAULT_JAR)
    parser.add_argument("--java", type=Path, default=DEFAULT_JAVA)
    parser.add_argument("--min-tokens", type=int, default=5)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    print(prepare(args.dataset.resolve(), args.output.resolve(), execute=args.execute, jar=args.jar.resolve(),
                  java=args.java.resolve(), min_tokens=args.min_tokens)["status"])
