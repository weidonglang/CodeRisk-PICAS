"""Acquire pinned CodeXGLUE BCB pairs for external research intake; never score or execute code."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import heapq
import json
from pathlib import Path
import re
import urllib.request

from acquire_public_datasets import digest, store, text_digest, write_json, write_rows

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "ac74a62802a0dd159b3258c78a2df8ad36cdf2b9"
DATA_PATH = "Code-Code/Clone-detection-BigCloneBench/dataset/"
RAW_BASE = f"https://raw.githubusercontent.com/microsoft/CodeXGLUE/{COMMIT}/"
PINS = {
    "data.jsonl": (DATA_PATH + "data.jsonl", 15174797, "21f3cf5b0fb1d57db28b6bf8cacd2933e91f4bbc"),
    "train.txt": (DATA_PATH + "train.txt", 17043552, "33a19e93151999b7e4ad46ad27a952d7b6584884"),
    "valid.txt": (DATA_PATH + "valid.txt", 7861019, "9175d2fe7f6d5aefa3579ed5027b1b7050bbd7bd"),
    "test.txt": (DATA_PATH + "test.txt", 7876506, "42f7d44cc954276b12f156a74659b9e0b5ea9feb"),
    "dataset_README.md": ("Code-Code/Clone-detection-BigCloneBench/README.md", 5125, "31239199af516a6a745b9e390147de31f11687e2"),
    "repository_README.md": ("README.md", 11372, "0a50f46fb881105ce20177502cc28a8223a26d89"),
    "Data_LICENCE": ("Data_LICENCE", 7060, "2a9479b291d0f565a518cf1935f790c4354864c5"),
    "LICENSE": ("LICENSE", 1141, "9e841e7a26e4eb057b24511e7b92d42b257a80e5"),
}
SPLITS = ("train", "valid", "test")
EXPECTED_ROWS = {"train": 901028, "valid": 415416, "test": 415416}


def verify_blob(data: bytes, size: int, blob: str) -> None:
    actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if len(data) != size or actual != blob:
        raise ValueError("Pinned Git blob or byte length mismatch; do not silently update the pin")


def fetch_pinned(cache: Path, name: str, offline: bool) -> bytes:
    path, size, blob = PINS[name]
    target = cache / name
    if not target.exists():
        if offline:
            raise FileNotFoundError(f"Missing pinned cache file: {name}")
        cache.mkdir(parents=True, exist_ok=True)
        temporary = cache / (name + ".part")
        request = urllib.request.Request(RAW_BASE + path, headers={"User-Agent": "CodeRisk-public-research-intake/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as handle:
            count = 0
            while chunk := response.read(256 * 1024):
                count += len(chunk)
                if count > size:
                    raise ValueError("Download exceeded pinned byte length")
                handle.write(chunk)
        verify_blob(temporary.read_bytes(), size, blob)
        temporary.replace(target)
    data = target.read_bytes()
    verify_blob(data, size, blob)
    return data


def load_functions(path: Path) -> dict[str, dict]:
    sources = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            row = json.loads(line)
            idx, code = str(row["idx"]), row["func"]
            if not re.fullmatch(r"[0-9]+", idx) or idx in sources:
                raise ValueError(f"Invalid or repeated function idx at line {line_number}")
            if not isinstance(code, str) or not code.strip():
                raise ValueError(f"Empty/non-text function: {idx}")
            raw = code.encode("utf-8")
            sources[idx] = {"upstream_idx": idx, "code": code, "code_sha256_bytes": digest(raw),
                            "code_sha256_text": text_digest(raw)}
    if not sources or len(sources) > 12000:
        raise ValueError("Function count exceeds bounded BCB intake policy")
    return sources


def iter_pairs(path: Path, sources: dict[str, dict]):
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            fields = line.split()
            if len(fields) != 3 or fields[2] not in {"0", "1"}:
                raise ValueError(f"Malformed published pair: {path.name}:{number}")
            a, b, label = fields
            if a not in sources or b not in sources:
                raise ValueError(f"Unresolved function reference: {path.name}:{number}")
            yield number, a, b, int(label)


def source_record(source: dict) -> dict:
    return {key: value for key, value in source.items() if key != "code"} | {
        "source_id": "BCB-SRC-" + source["upstream_idx"],
        "code_path": f"sources/{source['upstream_idx']}.java", "language": "java",
        "function_fragment": True, "problem_id": None, "source_type": "external",
        "synthetic": False, "eligible_for_core_metrics": False, "source_executed": False,
    }


def pair_index(a: int, b: int, size: int) -> int:
    a, b = sorted((a, b))
    return a * (2 * size - a - 1) // 2 + b - a - 1


def audit_and_select(upstream: Path, sources: dict, target: int, seed: int) -> tuple[dict, list[dict]]:
    if target < 2 or target % 2:
        raise ValueError("Pair target must be a positive even number >= 2")
    hashes = sorted({row["code_sha256_text"] for row in sources.values()})
    hash_ids = {value: index for index, value in enumerate(hashes)}
    ids = {idx: hash_ids[row["code_sha256_text"]] for idx, row in sources.items()}
    size = len(hashes)
    # Upper-triangle byte flags bound memory to <72 MB for the pinned <=12k functions.
    states = bytearray(size * (size - 1) // 2)
    source_sets, hash_sets, stats = {}, {}, {}
    conflicts, cross_split_pairs = 0, 0
    for split_no, split in enumerate(SPLITS):
        counts = Counter()
        source_sets[split], hash_sets[split] = set(), set()
        split_bit = 1 << (split_no + 2)
        for _, a, b, label in iter_pairs(upstream / f"{split}.txt", sources):
            counts["rows"] += 1
            counts[f"published_label_{label}"] += 1
            source_sets[split].update((a, b))
            hash_sets[split].update((ids[a], ids[b]))
            if a == b:
                counts["self_id_rows"] += 1
            if ids[a] == ids[b]:
                counts["identical_text_rows_excluded"] += 1
                continue
            key = pair_index(ids[a], ids[b], size)
            previous = states[key]
            if previous & split_bit:
                counts["duplicate_or_reversed_text_pair_rows"] += 1
            else:
                counts["unique_nonidentical_text_pairs"] += 1
            if previous & 3 != 3 and previous & 3 and previous & 3 != 1 << label:
                conflicts += 1
            prior_splits = previous >> 2
            if not previous & split_bit and prior_splits.bit_count() == 1:
                cross_split_pairs += 1
            states[key] |= (1 << label) | split_bit
        stats[split] = dict(counts)
    overlaps = []
    for i, a in enumerate(SPLITS):
        for b in SPLITS[i + 1:]:
            overlaps.append({"split_a": a, "split_b": b,
                             "shared_function_ids": len(source_sets[a] & source_sets[b]),
                             "shared_text_hashes": len(hash_sets[a] & hash_sets[b])})

    # Hash-ranked published train pairs only. Selection uses labels/identity, never PICAS scores.
    heaps = {0: [], 1: []}
    seen, available = set(), Counter()
    for line, a, b, label in iter_pairs(upstream / "train.txt", sources):
        if ids[a] == ids[b]:
            continue
        key = pair_index(ids[a], ids[b], size)
        if key in seen or states[key] & 3 == 3:
            continue
        seen.add(key)
        available[label] += 1
        first, second = sorted((sources[a]["code_sha256_text"], sources[b]["code_sha256_text"]))
        rank = int(digest(f"{seed}:{first}:{second}".encode()), 16)
        item = (-rank, -key, a, b, line)
        if len(heaps[label]) < target // 2:
            heapq.heappush(heaps[label], item)
        elif item > heaps[label][0]:
            heapq.heapreplace(heaps[label], item)
    if any(len(heaps[label]) != target // 2 for label in (0, 1)):
        raise ValueError(f"Insufficient distinct nonconflicting published train pairs: {dict(available)}")
    selected = []
    for label, items in heaps.items():
        for negative_rank, _, a, b, line in items:
            first, second = sorted((sources[a]["code_sha256_text"], sources[b]["code_sha256_text"]))
            identity = digest(f"{first}:{second}".encode())
            selected.append({
                "pair_id": "BCB-" + identity[:32], "dataset": "codexglue-bcb",
                "dataset_version": "codexglue-bcb-" + COMMIT[:12],
                "source_a": "BCB-SRC-" + a, "source_b": "BCB-SRC-" + b,
                "code_a_path": f"sources/{a}.java", "code_b_path": f"sources/{b}.java",
                "code_a_sha256_bytes": sources[a]["code_sha256_bytes"],
                "code_b_sha256_bytes": sources[b]["code_sha256_bytes"],
                "code_a_sha256_text": sources[a]["code_sha256_text"],
                "code_b_sha256_text": sources[b]["code_sha256_text"],
                "language": "java", "source_type": "external", "synthetic": False,
                "upstream_split": "train", "upstream_line": line, "published_label": label,
                "relationship_basis": "PUBLISHER_BINARY_CODE_CLONE_LABEL",
                "experiment_label": "UNCERTAIN", "case_type": None,
                "dataset_split": "development", "problem_id": None,
                "problem_metadata_status": "NOT_PROVIDED_BY_THIS_RELEASE",
                "source_family_status": "AUTHOR_AND_PROJECT_FAMILIES_UNKNOWN",
                "source_disjoint_evaluation_status": "NOT_ESTABLISHED",
                "eligible_for_core_metrics": False, "local_human_reviews": 0,
                "selection_rank": f"{(-negative_rank):064x}", "source_executed": False,
                "notes": "Function fragments. Public clone label is not a plagiarism/independence label. No local semantic verification.",
            })
    selected.sort(key=lambda row: (row["published_label"], row["selection_rank"], row["pair_id"]))
    report = {
        "upstream_split_counts": stats, "upstream_total_pair_rows": sum(row["rows"] for row in stats.values()),
        "unique_nonidentical_text_pairs_across_splits": sum(bool(value) for value in states),
        "conflicting_text_pair_labels_quarantined": conflicts,
        "text_pairs_in_multiple_upstream_splits": cross_split_pairs,
        "upstream_source_overlap": overlaps, "problem_disjoint_verified": False,
        "available_train_unique_pairs_by_published_label": dict(available),
        "selected_pair_count": len(selected), "selected_labels": dict(Counter(row["published_label"] for row in selected)),
        "selected_distinct_text_pairs": len({(min(row["code_a_sha256_text"], row["code_b_sha256_text"]), max(row["code_a_sha256_text"], row["code_b_sha256_text"])) for row in selected}),
        "selected_referenced_function_ids": len({row[key] for row in selected for key in ("source_a", "source_b")}),
        "selection_policy": "Balanced labels; lowest SHA256(seed:ordered_text_hashes) from published train only; identical-text and contradictory-label pairs excluded.",
        "selection_uses_detector_scores": False, "formal_eligible_pairs": 0,
    }
    return report, selected


def intake(cache: Path, output: Path, target: int, seed: int, offline: bool) -> dict:
    if output.exists():
        raise FileExistsError("Use a new output directory, or --verify-only for existing data")
    files = {}
    for name in PINS:
        data = fetch_pinned(cache, name, offline)
        files[name] = {"sha256": digest(data), "size_bytes": len(data), "git_blob_sha1": PINS[name][2],
                       "url": RAW_BASE + PINS[name][0]}
        print(f"Verified pinned input: {name} ({len(data)} bytes)", flush=True)
    sources = load_functions(cache / "data.jsonl")
    report, pairs = audit_and_select(cache, sources, target, seed)
    if {split: report["upstream_split_counts"][split]["rows"] for split in SPLITS} != EXPECTED_ROWS:
        raise ValueError("Pinned input row counts differ from publisher statistics")
    output.mkdir(parents=True)
    for name in PINS:
        store(output / "upstream" / name, (cache / name).read_bytes())
    registry = []
    for idx, source in sorted(sources.items()):
        path = f"sources/{idx}.java"
        store(output / path, source["code"].encode("utf-8"))
        registry.append(source_record(source))
    write_rows(output / "source_registry.jsonl", registry)
    write_rows(output / "selected_pairs.jsonl", pairs)
    report["function_source_records"] = len(sources)
    report["unique_function_text_hashes"] = len({source["code_sha256_text"] for source in sources.values()})
    report["unique_function_byte_hashes"] = len({source["code_sha256_bytes"] for source in sources.values()})
    write_json(output / "audit_summary.json", report)
    manifest = {
        "status": "EXTERNAL_PUBLIC_CLONE_DATA_INTAKE_NOT_FORMAL_EVALUATION",
        "dataset": "codexglue-bcb", "source_commit": COMMIT, "client_work_date": "2026-10-10",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": seed, "requested_pair_count": target,
        "source_repository": "https://github.com/microsoft/CodeXGLUE",
        "upstream_files": files, "summary": report,
        "license_record": {
            "publisher_dataset_declaration": "C-UDA (repository README)",
            "code_license": "MIT (LICENSE); not automatically a license for all upstream functions",
            "supplied_Data_LICENCE_observation": "Pinned Data_LICENCE contains CC0 text for microsoft/Computational-Use-of-Data-Agreement; this does not independently clear every original source license.",
            "redistribution_policy": "Raw sources remain local and Git-ignored. Preserve publisher and original-source limitations.",
        },
        "registry_sha256": {name: digest((output / name).read_bytes()) for name in ("source_registry.jsonl", "selected_pairs.jsonl", "audit_summary.json")},
        "algorithm_changed": False, "detector_scored_pairs": 0, "formal_eligible_pairs": 0,
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def verify(output: Path) -> dict:
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if manifest["source_commit"] != COMMIT or manifest["formal_eligible_pairs"] != 0:
        raise ValueError("Intake provenance/eligibility changed")
    upstream = output / "upstream"
    for name, (_, size, blob) in PINS.items():
        data = (upstream / name).read_bytes()
        verify_blob(data, size, blob)
        if digest(data) != manifest["upstream_files"][name]["sha256"]:
            raise ValueError("Recorded upstream hash mismatch")
    sources = load_functions(upstream / "data.jsonl")
    report, pairs = audit_and_select(upstream, sources, manifest["requested_pair_count"], manifest["random_seed"])
    stored = [json.loads(line) for line in (output / "selected_pairs.jsonl").read_text(encoding="utf-8").splitlines()]
    if stored != pairs:
        raise ValueError("Selected pair identities/labels differ from pinned reconstruction")
    registry = [json.loads(line) for line in (output / "source_registry.jsonl").read_text(encoding="utf-8").splitlines()]
    expected_registry = [source_record(source) for _, source in sorted(sources.items())]
    if registry != expected_registry:
        raise ValueError("Source registry differs from pinned reconstruction")
    for row in registry:
        idx = row["upstream_idx"]
        source = sources[idx]
        path = (output / row["code_path"]).resolve()
        if not path.is_relative_to(output.resolve()) or path.read_bytes() != source["code"].encode("utf-8"):
            raise ValueError(f"Source content/path changed: {idx}")
        if row["code_sha256_bytes"] != source["code_sha256_bytes"] or row["code_sha256_text"] != source["code_sha256_text"] or row["eligible_for_core_metrics"]:
            raise ValueError(f"Source metadata changed: {idx}")
    report["function_source_records"] = len(sources)
    report["unique_function_text_hashes"] = len({source["code_sha256_text"] for source in sources.values()})
    report["unique_function_byte_hashes"] = len({source["code_sha256_bytes"] for source in sources.values()})
    for key, value in report.items():
        # JSON object keys normalize integer labels to strings.
        if json.loads(json.dumps(value)) != manifest["summary"][key]:
            raise ValueError(f"Audit summary changed: {key}")
    for name, expected in manifest["registry_sha256"].items():
        if digest((output / name).read_bytes()) != expected:
            raise ValueError(f"Registry changed: {name}")
    return {"verified": True, "function_sources": len(sources), "selected_pairs": len(pairs),
            "upstream_pair_rows": report["upstream_total_pair_rows"], "formal_eligible_pairs": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/public-datasets/codexglue-bcb-20261010")
    parser.add_argument("--cache", type=Path, default=ROOT.parent / ".tmp/codexglue-bcb-pinned")
    parser.add_argument("--pairs", type=int, default=30000)
    parser.add_argument("--seed", type=int, default=20261010)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(args.output.resolve()), ensure_ascii=True))
    else:
        result = intake(args.cache.resolve(), args.output.resolve(), args.pairs, args.seed, args.offline)
        print(json.dumps(result["summary"], ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
