from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_v4_dataset import DatasetValidationError, load_research_dataset, write_validation_artifacts


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Research V4 metadata and split isolation.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "experiment/datasets/research-v4/dataset.json",
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    try:
        manifest, cases, report = load_research_dataset(args.manifest, raise_on_error=True)
    except DatasetValidationError as error:
        print(json.dumps(error.report, ensure_ascii=False, indent=2))
        return 2
    if args.output_dir:
        write_validation_artifacts(args.output_dir.resolve(), manifest, cases, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
