from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def convert(input_path: Path, output_path: Path) -> int:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if payload.get("tool") != "JPLAG":
        raise ValueError("Input tool must be JPLAG")
    version = str(payload.get("toolVersion", "")).strip()
    if not version:
        raise ValueError("toolVersion is required")
    comparisons = payload.get("comparisons")
    if not isinstance(comparisons, list):
        raise ValueError("comparisons must be a list")

    rows = []
    for comparison in comparisons:
        case_id = str(comparison.get("caseId", "")).strip()
        score = comparison.get("similarity")
        if not case_id or not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
            raise ValueError("Each comparison requires caseId and similarity in [0, 1]")
        rows.append(
            {
                "caseId": case_id,
                "method": "JPLAG",
                "methodVersion": version,
                "predictedScore": round(float(score), 6),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["caseId", "method", "methodVersion", "predictedScore"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def convert_native_csv(input_path: Path, output_path: Path, version: str) -> int:
    if not version.strip():
        raise ValueError("toolVersion is required for native JPlag CSV")
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        native_rows = list(csv.DictReader(handle))

    rows = []
    for item in native_rows:
        left = str(item.get("submissionName1", "")).strip()
        right = str(item.get("submissionName2", "")).strip()
        raw_score = item.get("averageSimilarity")
        if not left or not right or raw_score is None:
            raise ValueError("Native JPlag CSV requires submissionName1, submissionName2, and averageSimilarity")
        score = float(raw_score)
        if not 0 <= score <= 1:
            raise ValueError("JPlag averageSimilarity must be in [0, 1]")
        rows.append({
            "caseId": f"{left}__{right}",
            "method": "JPLAG",
            "methodVersion": version.strip(),
            "predictedScore": round(score, 6),
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["caseId", "method", "methodVersion", "predictedScore"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a neutral JPlag export to the CodeRisk baseline contract.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--input-format", choices=["neutral-json", "jplag-csv"], default="neutral-json")
    parser.add_argument("--tool-version", default="")
    args = parser.parse_args()
    count = (
        convert_native_csv(args.input, args.output, args.tool_version)
        if args.input_format == "jplag-csv"
        else convert(args.input, args.output)
    )
    print(json.dumps({"output": str(args.output), "rowCount": count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
