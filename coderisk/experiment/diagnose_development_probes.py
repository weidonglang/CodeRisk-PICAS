"""Diagnose production fusion on explicit synthetic development probes; never fit parameters."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis-service-python"))

from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.token_similarity import (
    _fingerprints, _ngram_size, analyze_token_pair, parse_ast_nodes, tokenize_code_with_locations,
)
from app.schemas.analyze_schema import AnalyzeMockRequest

DEFAULT_PROBES = ROOT / "experiment/datasets/development-fusion-probes/probes.json"


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def inspect_side(code: str, language: str) -> dict:
    tokens = tokenize_code_with_locations(code, language)
    canonical = canonicalize_code(code, language, tokens)
    parsed = parse_ast_nodes(code, language)
    return {
        "code": code, "code_sha256": digest(code.encode("utf-8")),
        "raw_tokens": [token.value for token in tokens], "canonical_tokens": canonical.tokens,
        "canonical_mode": canonical.mode, "canonical_reason": canonical.reason,
        "identifiers": canonical.identifiers, "ast_parsed": parsed.parsed,
        "ast_error": parsed.error, "ast_nodes": [node.value for node in parsed.nodes],
    }


def compare_probe(probe: dict, bases: dict) -> dict:
    code_a = probe.get("code_a", bases.get(probe.get("base")))
    code_b = probe["code_b"]
    if not isinstance(code_a, str) or not code_a.strip() or not code_b.strip():
        raise ValueError(f"Empty probe source: {probe['pair_id']}")
    language = probe["language"]
    left, right = inspect_side(code_a, language), inspect_side(code_b, language)
    result = analyze_token_pair(AnalyzeMockRequest.model_validate({
        "question": {"id": 1, "title": "Synthetic development probe",
                     "description": "Self-authored static comparison for fusion diagnosis."},
        "submissionA": {"id": 1, "language": language, "code": code_a},
        "submissionB": {"id": 2, "language": language, "code": code_b},
        "config": {"mode": "PICAS_STANDARD"},
    }))
    fusion_enabled = next(metric for metric in result.metrics if metric.name == "CANONICAL_TOKEN_SIMILARITY").weight > 0
    raw, ast = result.token_similarity, result.ast_similarity
    baseline = .5 * (raw + ast) if fusion_enabled else raw
    canonical_contribution = .45 * (result.canonical_token_similarity - .5 * (raw + ast)) if fusion_enabled else 0.
    mapping_contribution = .15 * (result.identifier_mapping_similarity - .5 * (raw + ast)) if fusion_enabled else 0.
    delta = result.weighted_similarity_score - baseline
    if abs(delta - canonical_contribution - mapping_contribution) > 2e-6:
        raise ValueError("Production formula changed; update diagnostic protocol before interpreting results")
    if abs(sum(metric.weight * metric.value for metric in result.metrics) - result.weighted_similarity_score) > 2e-6:
        raise ValueError("Returned metric weights do not reconstruct the production score")
    contract = probe["contract"]
    if contract not in {"canonical_equal", "raw_fallback", "observe"}:
        raise ValueError(f"Unknown probe contract: {contract}")
    contract_passed = (
        fusion_enabled and left["canonical_tokens"] == right["canonical_tokens"]
        and result.canonical_token_similarity == 1.
        if contract == "canonical_equal" else
        not fusion_enabled and result.weighted_similarity_score == raw
        and not any(item.evidence_type in {"IDENTIFIER_MAPPING", "CANONICAL_TOKEN_MATCH"} for item in result.evidence)
        if contract == "raw_fallback" else None
    )
    fingerprints = {}
    for name, key in (("raw", "raw_tokens"), ("canonical", "canonical_tokens"), ("ast", "ast_nodes")):
        first, second = _fingerprints(left[key]), _fingerprints(right[key])
        fingerprints[name] = {"ngram_a": _ngram_size(len(left[key])), "ngram_b": _ngram_size(len(right[key])),
                              "unique_a": len(first), "unique_b": len(second),
                              "intersection": len(first & second), "union": len(first | second)}
    return {
        "pair_id": probe["pair_id"], "language": language, "kind": probe["kind"],
        "contract": contract, "contract_passed": contract_passed,
        "source_type": "synthetic", "eligible_for_core_metrics": False,
        "raw": raw, "ast": ast, "canonical": result.canonical_token_similarity,
        "mapping": result.identifier_mapping_similarity, "full": result.weighted_similarity_score,
        "no_canonical_same_pair": baseline, "fusion_enabled": fusion_enabled,
        "canonical_contribution": canonical_contribution, "mapping_contribution": mapping_contribution,
        "fusion_change": delta, "fingerprints": fingerprints,
        "left": left, "right": right, "production_result": result.model_dump(by_alias=True),
    }


def run(probes_path: Path, output: Path) -> dict:
    data = json.loads(probes_path.read_text(encoding="utf-8"))
    if data.get("source_type") != "synthetic" or data.get("eligible_for_core_metrics") is not False:
        raise ValueError("Development probes must be synthetic and excluded from core metrics")
    ids = [probe["pair_id"] for probe in data["probes"]]
    if not ids or any(not isinstance(value, str) or not value.strip() for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("Development probes must have unique, nonempty pair IDs")
    if output.exists():
        raise FileExistsError("Use a fresh output directory; prior diagnostic records are immutable")
    records = [compare_probe(probe, data["bases"]) for probe in data["probes"]]
    output.mkdir(parents=True)
    (output / "pair_diagnostics.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = ["pair_id", "language", "kind", "contract", "contract_passed", "source_type",
              "eligible_for_core_metrics", "raw", "ast", "canonical", "mapping", "full",
              "no_canonical_same_pair", "fusion_enabled", "canonical_contribution", "mapping_contribution", "fusion_change"]
    with (output / "component_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    lines = ["# Synthetic development fusion diagnostics", "",
             "Self-authored probes after observing ConPlag. No held-out accuracy, fitting, or benchmark claim.", "",
             "Full - no-canonical = .45*(C-.5*(R+A)) + .15*(M-.5*(R+A)); fallback uses raw on both sides.", "",
             "| Pair | Raw | AST | Canonical | Mapping | Full | No-canonical | Delta | Contract |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for row in records:
        values = " | ".join(f"{row[field]:.6f}" for field in ("raw", "ast", "canonical", "mapping", "full", "no_canonical_same_pair", "fusion_change"))
        lines.append(f"| {row['pair_id']} | {values} | {row['contract_passed']} |")
    lines.extend(["", "Null contract means descriptive observation, not a passed invariance test.",
                  "All production thresholds/weights are unchanged. Sources are inspected as text, never executed.", ""])
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    git_status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    sources = sorted((ROOT / "analysis-service-python/app").rglob("*.py")) + [Path(__file__), probes_path]
    source_hashes = {path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix(): digest(path.read_bytes()) for path in sources}
    manifest = {
        "run_id": output.name, "dataset_version": data["dataset_version"], "source_type": "synthetic",
        "purpose": data["purpose"], "eligible_for_core_metrics": False, "probe_count": len(records),
        "formula_version": "FORMULA_SPEC_V1", "algorithm_version": "picas-v2-rule-1.0",
        "local_version_fingerprint": digest(json.dumps(source_hashes, sort_keys=True).encode()),
        "git_commit": git.stdout.strip() if git.returncode == 0 else None,
        "git_dirty": bool(git_status.stdout.strip()) if git_status.returncode == 0 else None,
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "client_work_date": "2026-10-10",
        "python_version": platform.python_version(), "random_seed": None,
        "production_formula_changed": False, "public_test_rescored": False,
        "parameter_fitting": False, "source_sha256": source_hashes,
        "contract_checks": sum(row["contract_passed"] is not None for row in records),
        "failed_contracts": [row["pair_id"] for row in records if row["contract_passed"] is False],
        "output_sha256": {path.name: digest(path.read_bytes()) for path in output.iterdir()},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probes", type=Path, default=DEFAULT_PROBES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = run(args.probes.resolve(), args.output.resolve())
    print(json.dumps({key: manifest[key] for key in ("run_id", "probe_count", "contract_checks", "failed_contracts")}))
    return 1 if manifest["failed_contracts"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
