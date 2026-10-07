from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from research_v4_dataset import VALID_CASE_TYPES


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = ROOT / "experiment/datasets/research-v4"


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    dataset_root = args.dataset_root.resolve()
    entry, pending = build_entry(args, dataset_root)
    result: dict[str, Any] = {
        "entry": entry,
        "pending_confirmation_fields": pending,
        "appendRequested": args.append,
        "appended": False,
    }
    if args.append:
        if pending:
            result["error"] = "Resolve pending_confirmation_fields before appending."
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2
        shard = dataset_root / "pairs/manual_pairs.json"
        append_entry(shard, entry)
        result["appended"] = True
        result["manifestShard"] = str(shard)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_entry(args: argparse.Namespace, dataset_root: Path) -> tuple[dict[str, Any], list[str]]:
    code_a_path = _safe_path(dataset_root, Path(args.code_a))
    code_b_path = _safe_path(dataset_root, Path(args.code_b))
    code_a = code_a_path.read_text(encoding="utf-8")
    code_b = code_b_path.read_text(encoding="utf-8")
    pending: list[str] = []
    for name in ("title", "description"):
        if not str(getattr(args, name, "") or "").strip():
            pending.append(name)
    if args.source_type in {"manual", "ai_assisted", "external"} and not args.license_or_authorization:
        pending.append("license_or_authorization")
    if args.source_type == "ai_assisted" or args.case_type == "AI_REWRITE":
        for name in ("model_name", "prompt_template", "generation_time"):
            if not str(getattr(args, name, "") or "").strip():
                pending.append(name)
        if args.manual_check_status != "VERIFIED":
            pending.append("manual_check_status=VERIFIED")
        if args.functional_check_status != "PASSED":
            pending.append("functional_check_status=PASSED")

    requested_eligible = bool(args.eligible_for_core_metrics)
    eligible = requested_eligible and not pending and args.experiment_label != "UNCERTAIN"
    synthetic = args.source_type in {"synthetic", "placeholder"}
    data_origin = {
        "synthetic": "SYNTHETIC",
        "placeholder": "SYNTHETIC",
        "manual": "MANUAL",
        "ai_assisted": "MANUAL",
        "external": "PUBLIC",
    }[args.source_type]
    language = args.language_a if args.language_a == args.language_b else f"{args.language_a}-{args.language_b}"
    entry = {
        "pair_id": args.pair_id,
        "problem_id": args.problem_id,
        "problem_type": args.problem_type,
        "problem_group": args.problem_group,
        "dataset_split": args.dataset_split,
        "split_preregistered": True,
        "source_id": args.source_id,
        "experiment_label": args.experiment_label,
        "case_type": args.case_type,
        "language": language,
        "language_a": args.language_a,
        "language_b": args.language_b,
        "dataset_version": args.dataset_version,
        "data_origin": data_origin,
        "source_type": args.source_type,
        "synthetic": synthetic,
        "eligible_for_core_metrics": eligible,
        "question": {
            "title": args.title or "PENDING HUMAN CONFIRMATION",
            "description": args.description or "PENDING HUMAN CONFIRMATION",
            "input_format": args.input_format or "",
            "output_format": args.output_format or "",
            "constraints_text": args.constraints_text or "",
        },
        "code_a_path": code_a_path.relative_to(dataset_root).as_posix(),
        "code_b_path": code_b_path.relative_to(dataset_root).as_posix(),
        "code_a_sha256": _sha256(code_a),
        "code_b_sha256": _sha256(code_b),
        "provenance": {
            "source": args.provenance_source or args.source_type,
            "license_or_authorization": args.license_or_authorization or "PENDING HUMAN CONFIRMATION",
            "model_name": args.model_name or "",
            "prompt_template": args.prompt_template or "",
            "temperature": args.temperature,
            "generation_time": args.generation_time or "",
            "manual_check_status": args.manual_check_status,
            "functional_check_status": args.functional_check_status,
        },
        "notes": args.notes or "",
    }
    if requested_eligible and not eligible:
        pending.append("eligible_for_core_metrics blocked until pending fields are resolved")
    return entry, sorted(set(pending))


def append_entry(shard_path: Path, entry: dict[str, Any]) -> None:
    payload = json.loads(shard_path.read_text(encoding="utf-8"))
    cases = payload.setdefault("cases", [])
    if any(case.get("pair_id") == entry["pair_id"] for case in cases):
        raise ValueError(f"Duplicate pair_id: {entry['pair_id']}")
    cases.append(entry)
    shard_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _safe_path(dataset_root: Path, value: Path) -> Path:
    path = value.resolve() if value.is_absolute() else (dataset_root / value).resolve()
    if not path.is_relative_to(dataset_root):
        raise ValueError(f"Code path escapes the Research V4 dataset root: {value}")
    if not path.is_file():
        raise ValueError(f"Code file does not exist: {value}")
    return path


def _sha256(code: str) -> str:
    return "sha256:" + hashlib.sha256(code.encode("utf-8")).hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or append one Research V4 manual manifest entry.")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--dataset-version", default="coderisk-research-v4-seed-1.0")
    parser.add_argument("--pair-id", required=True)
    parser.add_argument("--problem-id", required=True)
    parser.add_argument("--problem-type", required=True)
    parser.add_argument("--problem-group", choices=["G1", "G2", "G3", "G4"], required=True)
    parser.add_argument("--dataset-split", choices=["validation", "test"], required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-type", choices=["manual", "synthetic", "ai_assisted", "external", "placeholder"], required=True)
    parser.add_argument("--experiment-label", choices=["SIMILAR", "SUSPICIOUS", "TRANSFORMED", "INDEPENDENT", "NATURAL_SIMILAR", "UNCERTAIN"], required=True)
    parser.add_argument("--case-type", choices=sorted(VALID_CASE_TYPES), required=True)
    parser.add_argument("--language-a", choices=["java", "python", "c"], required=True)
    parser.add_argument("--language-b", choices=["java", "python", "c"], required=True)
    parser.add_argument("--code-a", required=True)
    parser.add_argument("--code-b", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--input-format", default="")
    parser.add_argument("--output-format", default="")
    parser.add_argument("--constraints-text", default="")
    parser.add_argument("--provenance-source", default="")
    parser.add_argument("--license-or-authorization", default="")
    parser.add_argument("--model-name", default="")
    parser.add_argument("--prompt-template", default="")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--generation-time", default="")
    parser.add_argument("--manual-check-status", choices=["VERIFIED", "PENDING", "REJECTED"], default="PENDING")
    parser.add_argument("--functional-check-status", choices=["PASSED", "FAILED", "NOT_RUN"], default="NOT_RUN")
    parser.add_argument("--notes", default="")
    parser.add_argument("--eligible-for-core-metrics", action="store_true")
    parser.add_argument("--append", action="store_true")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
