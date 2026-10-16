"""Validate and snapshot a user-provided LOCAL export; no live adapter exists."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_convergence.protocol import safe_file, write_json, require_private_output
from ai_convergence.validate import validate


def ingest(source, output, *, dry_run=False):
    corpus, _, report = validate(source)
    if any(ref in {"corpus.json", "ingest_report.json"} for ref in report["file_sha256"]):
        raise ValueError("Imported reserved snapshot filename rejected")
    if output.exists():
        raise FileExistsError("Fresh immutable output required")
    if dry_run:
        return report
    # Real raw data is only accepted under the ignored local research output tree.
    require_private_output(any(not sample.synthetic for sample in corpus.artifacts), output)
    output.mkdir(parents=True)
    for ref in report["file_sha256"]:
        target = output / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe_file(source.parent, ref), target)
    write_json(output / "corpus.json", corpus.model_dump())
    write_json(output / "ingest_report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--no-network", action="store_true", help="Always offline; flag documents intent")
    args = parser.parse_args()
    report = ingest(args.input.resolve(), args.output.resolve(), dry_run=args.dry_run or args.validate_only)
    print({key: report[key] for key in ("status", "sample_count", "session_count", "network_calls")})


if __name__ == "__main__":
    main()
