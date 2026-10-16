"""Allowlist-only aggregate export: no raw code, prompts, session IDs or private paths."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_convergence.protocol import digest, write_json
from run_fair_evaluation import write_csv


def export(run_dir, output, *, minimum_cell_size=5):
    if type(minimum_cell_size) is not int or minimum_cell_size < 5:
        raise ValueError("Real aggregate cells require minimum size at least five")
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    with (run_dir / "distributions.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    output.mkdir(parents=True, exist_ok=False)
    synthetic = manifest["status"] == "DEVELOPMENT_ONLY"
    safe, suppressed = [], 0
    for row in rows:
        if not synthetic and int(row["n_available"]) < minimum_cell_size:
            suppressed += 1
            continue
        safe.append({"dimension": row["dimension"], "group_alias": "G-" + digest(row["group"].encode())[:16],
            "method": row["method"], **{key: row[key] for key in ("scope", "n_requested", "n_available", "n_missing", "mean", "median", "p90", "p95")}})
    write_csv(output / "aggregate_distributions.csv", safe)
    report = {"status": manifest["status"], "decision": manifest["decision"], "pair_count": manifest["pair_count"],
              "formal_eligible_pairs": manifest["formal_eligible_pairs"], "suppressed_cells": suppressed,
              "raw_code_included": False, "prompts_included": False, "student_or_session_ids_included": False,
              "publication_authorized_by_tool": False, "human_publication_review_required": True,
              "source_fingerprint": digest(json.dumps(manifest["source_sha256"], sort_keys=True).encode())}
    write_json(output / "public_summary.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(export(args.run_dir.resolve(), args.output.resolve())["status"])
