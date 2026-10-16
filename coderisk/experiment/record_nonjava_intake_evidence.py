"""Verify local intakes and preserve metadata-only evidence, never copying public code."""
import argparse
from collections import Counter
import json
from pathlib import Path
import platform
import shutil
import xml.etree.ElementTree as ET

from acquire_nonjava_datasets import ROOT, PINS_PATH, read_jsonl, verify
from acquire_public_datasets import digest, write_json


def summarize(registries: dict[str, list[dict]], pair_sets: dict[str, list[dict]]):
    records = [row for rows in registries.values() for row in rows]
    pairs = [row for rows in pair_sets.values() for row in rows]
    return {"new_source_records": len(records),
            "source_records_by_language": dict(sorted(Counter(row["language"] for row in records).items())),
            "unique_language_text_hashes": len({(row["language"], row["code_sha256_text"]) for row in records}),
            "raw_python_sources": len(registries["poolc"]),
            "tokenized_program_records": len(registries["xlcost"]),
            "raw_python_published_pairs": len(pair_sets["poolc"]),
            "unlabelled_title_aligned_cross_language_candidates": len(pair_sets["xlcost"]),
            "xlcost_candidates_without_java": sum("java" not in row["language"].split("/") for row in pair_sets["xlcost"]),
            "registered_pair_rows": len(pairs),
            "eligible_for_core_metrics": sum(bool(row["eligible_for_core_metrics"]) for row in pairs),
            "synthetic_pairs": sum(bool(row["synthetic"]) for row in pairs),
            "placeholder_pairs": sum(bool(row["placeholder"]) for row in pairs),
            "all_relation_labels_require_independent_review": True,
            "tokenized_programs_are_not_raw_source": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "experiment/evidence/nonjava-intake-20261010")
    parser.add_argument("--junit", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("Evidence output is immutable; choose a new directory")
    junit = ET.parse(args.junit).getroot()
    suites = [junit] if junit.tag == "testsuite" else list(junit.iter("testsuite"))
    tests = {key: sum(int(suite.get(key, "0")) for suite in suites)
             for key in ("tests", "failures", "errors", "skipped")}
    if tests["failures"] or tests["errors"] or tests["skipped"]:
        raise ValueError("Full successful regression evidence is required")
    results, registries, pairs = {}, {}, {}
    for kind in ("poolc", "xlcost"):
        source = ROOT / f"data/public-datasets/{kind}-20261010"
        results[kind] = verify(source)
        registries[kind] = read_jsonl(source / "source_registry.jsonl")
        pairs[kind] = read_jsonl(source / "selected_pairs.jsonl")
    summary = summarize(registries, pairs)
    output.mkdir(parents=True)
    snapshots = {}
    for kind in results:
        source = ROOT / f"data/public-datasets/{kind}-20261010"
        folder = output / kind
        folder.mkdir()
        for name in ("manifest.json", "audit_summary.json"):
            shutil.copyfile(source / name, folder / name)
            snapshots[f"{kind}/{name}"] = digest((folder / name).read_bytes())
    verifier = Path(__file__).with_name("acquire_nonjava_datasets.py")
    write_json(output / "collection_summary.json", summary)
    write_json(output / "verification.json", {
        "client_work_date": "2026-10-10", "status": "PINNED_INPUT_RECONSTRUCTION_VERIFIED",
        "verification_results": results, "snapshot_sha256": snapshots,
        "verifier_sha256": digest(verifier.read_bytes()), "pin_config_sha256": digest(PINS_PATH.read_bytes()),
        "python_version": platform.python_version(), "junit": {**tests, "path": str(args.junit.resolve()),
                                                                  "sha256": digest(args.junit.read_bytes())},
        "detector_scored_pairs": 0, "new_similarity_algorithms": 0,
        "production_weights_changed": False, "downloaded_code_executed": False,
        "backend_frontend_mysql_jplag_rerun": False})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
