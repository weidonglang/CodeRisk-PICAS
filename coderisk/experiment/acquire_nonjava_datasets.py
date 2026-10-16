"""Pinned Python pair intake and seven-language tokenized program intake, without scoring."""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path
import shutil
import time
import urllib.error
import warnings

from acquire_public_datasets import digest, fetch, store, text_digest, write_json, write_rows

ROOT = Path(__file__).resolve().parents[1]
PINS_PATH = Path(__file__).with_name("nonjava_dataset_pins.json")
PINS = json.loads(PINS_PATH.read_text(encoding="utf-8"))
LANGUAGES = {"C++": "cpp", "C": "c", "Csharp": "csharp", "Java": "java",
             "Javascript": "javascript", "PHP": "php", "Python": "python"}
MAX_CODE_BYTES = 2 * 1024 * 1024


def verify_pin(path: Path, pin: dict) -> None:
    if path.stat().st_size != pin["size"]:
        raise ValueError(f"Pinned size mismatch: {pin['path']}")
    data = path.read_bytes()
    if "sha256" in pin:
        valid = digest(data) == pin["sha256"]
    else:
        valid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == pin["git_blob"]
    if not valid:
        raise ValueError(f"Pinned hash mismatch: {pin['path']}")


def download(kind: str, cache: Path, offline: bool) -> None:
    spec = PINS[kind]
    for pin in spec["files"]:
        path = cache / pin["path"]
        if not path.exists():
            if offline:
                raise FileNotFoundError(f"Missing pinned offline input: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://huggingface.co/datasets/{spec['repository']}/resolve/{spec['revision']}/{pin['path']}"
            print(f"Downloading {kind}: {pin['path']} ({pin['size']} bytes)", flush=True)
            for attempt in range(3):
                try:
                    fetch(url, path, limit=pin["size"])
                    break
                except (urllib.error.URLError, TimeoutError, ConnectionError):
                    if attempt == 2:
                        raise
                    print(f"Transient download error; retry {attempt + 1}/2: {pin['path']}", flush=True)
                    time.sleep(2 * (attempt + 1))
        verify_pin(path, pin)
        print(f"Verified {kind}: {pin['path']}", flush=True)


def code_hash(code: str) -> str:
    if not isinstance(code, str) or not code.strip() or len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise ValueError("Empty, non-string or oversized code")
    return text_digest(code.encode("utf-8"))


def rank(seed: int, key: str) -> str:
    return digest(f"{seed}:{key}".encode())


def base_metadata(kind: str) -> dict:
    return {"source_type": "external", "synthetic": False, "placeholder": False,
            "dataset_version": PINS[kind]["revision"], "dataset_split": "development",
            "experiment_label": "UNCERTAIN", "case_type": None,
            "eligible_for_core_metrics": False, "local_human_review": "NOT_REVIEWED"}


def poolc_rows(path: Path):
    # Only the Parquet container is read. Never import a remote dataset loader or run source code.
    try:
        import pyarrow.parquet as parquet
    except ImportError as error:
        raise RuntimeError("Install experiment/requirements-intake.txt to read pinned Parquet") from error
    file = parquet.ParquetFile(path)
    expected = {"code1", "code2", "similar", "pair_id", "question_pair_id", "code1_group", "code2_group"}
    if set(file.schema_arrow.names) != expected:
        raise ValueError("Unexpected pinned PoolC schema")
    for batch in file.iter_batches(batch_size=4096):
        yield from batch.to_pylist()


def poolc_select(rows_factory, target: int, seed: int):
    if target < 2 or target % 2:
        raise ValueError("Python pair quota must be positive, even and at least two")
    masks, first, groups = {}, {}, defaultdict(set)
    counts = Counter()
    for index, row in enumerate(rows_factory(), 1):
        label = row["similar"]
        if type(label) is not int or label not in (0, 1):
            raise ValueError(f"Invalid publisher label at row {index}")
        counts["upstream_rows"] += 1
        try:
            hashes = [code_hash(row["code1"]), code_hash(row["code2"])]
        except ValueError:
            counts["invalid_or_oversized_code_rows_excluded"] += 1
            continue
        for side, value in zip((1, 2), hashes):
            group = row[f"code{side}_group"]
            if type(group) is not int or group < 0:
                raise ValueError("Invalid opaque publisher group")
            groups[value].add(group)
        if hashes[0] == hashes[1]:
            counts["identical_text_rows_excluded"] += 1
            continue
        key = ":".join(sorted(hashes))
        if key in masks:
            counts["duplicate_or_reversed_text_pair_rows"] += 1
        masks[key] = masks.get(key, 0) | (1 << label)
        first.setdefault(key, index)
    conflicts = {key for key, mask in masks.items() if mask == 3}
    choices = {}
    for label in (0, 1):
        available = [key for key, mask in masks.items() if mask == 1 << label]
        counts[f"available_unique_label_{label}"] = len(available)
        if len(available) < target // 2:
            raise ValueError(f"Insufficient non-conflicting Python pairs for label {label}")
        choices.update({first[key]: key for key in sorted(available, key=lambda key: (rank(seed, key), key))[:target // 2]})
    sources, pairs = {}, []
    for index, row in enumerate(rows_factory(), 1):
        if index not in choices:
            continue
        ids, hashes = [], []
        for side in (1, 2):
            code = row[f"code{side}"]
            sha = code_hash(code)
            sid = "POOLC-PY-" + sha
            ids.append(sid)
            hashes.append(sha)
            if sid not in sources:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", SyntaxWarning)
                        ast.parse(code)
                    syntax = "PYTHON3_PARSE_OK_NOT_EXECUTED"
                except (SyntaxError, ValueError, RecursionError):
                    syntax = "PYTHON3_PARSE_FAILED_POSSIBLE_PYTHON2_OR_UNSUPPORTED"
                sources[sid] = {**base_metadata("poolc"), "source_id": sid, "language": "python", "code": code,
                                "code_sha256_bytes": digest(code.encode()), "code_sha256_text": sha,
                                "upstream_groups": sorted(groups[sha]), "syntax_status": syntax,
                                "representation": "publisher_source_text", "source_family_id": None,
                                "problem_id": None, "upstream_split": "train"}
        pairs.append({**base_metadata("poolc"), "pair_id": "POOLC-PAIR-" + digest(choices[index].encode()),
                      "source_a": ids[0], "source_b": ids[1], "code_sha256_text_a": hashes[0],
                      "code_sha256_text_b": hashes[1], "language": "python", "problem_id": None,
                      "public_label": row["similar"], "upstream_split": "train", "upstream_shard": 0,
                      "upstream_row": index, "upstream_pair_id": row["pair_id"],
                      "upstream_question_pair_id": row["question_pair_id"],
                      "upstream_groups": [row["code1_group"], row["code2_group"]],
                      "label_basis": "publisher_similar_field_not_independent_local_review",
                      "license_status": "UNSPECIFIED_QUARANTINE_NO_FORMAL_USE"})
    counts["conflicting_text_pair_labels_quarantined"] = len(conflicts)
    counts["code_text_hashes_in_multiple_opaque_groups"] = sum(len(value) > 1 for value in groups.values())
    counts["selected_pairs"] = len(pairs)
    counts["selected_unique_source_texts"] = len(sources)
    report = {**dict(counts), "selected_labels": dict(Counter(row["public_label"] for row in pairs)),
              "selected_source_syntax": dict(Counter(row["syntax_status"] for row in sources.values())),
              "selected_code_group_count": len({g for row in sources.values() for g in row["upstream_groups"]}),
              "scope": "first_of_nine_upstream_train_shards_only_no_validation_download",
              "selection_uses_detector_scores": False, "formal_eligible_pairs": 0,
              "problem_disjoint_verified": False, "source_disjoint_verified": False,
              "validation_test_hash_isolation_verified": False}
    return sorted(sources.values(), key=lambda row: row["source_id"]), sorted(pairs, key=lambda row: row["pair_id"]), report


def xlcost_sources(upstream: Path):
    sources = []
    for publisher_language, language in LANGUAGES.items():
        for split in ("train", "valid", "test"):
            relpath = f"data/{publisher_language}-program-level/{split}.json"
            with (upstream / relpath).open(encoding="utf-8") as handle:
                for number, line in enumerate(handle, 1):
                    row = json.loads(line)
                    if set(row) != {"code", "text"} or not isinstance(row["text"], str):
                        raise ValueError(f"Unexpected XLCoST record: {relpath}:{number}")
                    # Some publisher rows end in ' |' with no comments after the separator.
                    title = row["text"].partition(" |")[0].strip() if " |" in row["text"] else None
                    title = title or None
                    sha = code_hash(row["code"])
                    sources.append({**base_metadata("xlcost"), "source_id": f"XLC-{language}-{split}-{number:05d}",
                                    "language": language, "upstream_split": split, "upstream_file": relpath,
                                    "upstream_row": number, "code": row["code"], "description": row["text"],
                                    "problem_title": title, "problem_id": None,
                                    "problem_title_key": digest(title.encode()) if title else None, "source_family_id": None,
                                    "title_status": "EXTRACTED_MIRROR_TITLE_NOT_OFFICIAL_ID" if title else "MISSING_SEPARATOR_NO_ALIGNMENT",
                                    "code_sha256_bytes": digest(row["code"].encode()), "code_sha256_text": sha,
                                    "representation": "publisher_tokenized_program_NOT_RAW_SOURCE",
                                    "syntax_status": "NOT_PARSED_TOKENIZED_INPUT", "license_status": "MIRROR_DECLARES_CC_BY_SA_4_0_ORIGINAL_RIGHTS_REVIEW_REQUIRED"})
    return sorted(sources, key=lambda row: row["source_id"])


def xlcost_candidates(sources: list[dict], per_language_pair: int, seed: int):
    if per_language_pair < 1:
        raise ValueError("Cross-language candidate quota must be positive")
    titles, hashes = defaultdict(list), defaultdict(set)
    for row in sources:
        if row["problem_title"]:
            titles[row["problem_title"]].append(row)
        hashes[(row["language"], row["code_sha256_text"])].add(row["upstream_split"])
    possible = defaultdict(list)
    reasons = Counter()
    for title, rows in sorted(titles.items()):
        if len({row["upstream_split"] for row in rows}) > 1:
            reasons["titles_across_upstream_splits_excluded"] += 1
            continue
        if rows[0]["upstream_split"] != "train":
            continue
        if len({row["language"] for row in rows}) != len(rows):
            reasons["ambiguous_same_language_titles_excluded"] += 1
            continue
        if any(len(hashes[(row["language"], row["code_sha256_text"])]) > 1 for row in rows):
            reasons["titles_with_split_shared_code_hashes_excluded"] += 1
            continue
        for a, b in combinations(sorted(rows, key=lambda row: row["language"]), 2):
            if a["code_sha256_text"] == b["code_sha256_text"]:
                reasons["identical_cross_language_token_text_excluded"] += 1
                continue
            key = f"{a['language']}:{a['code_sha256_text']}:{b['language']}:{b['code_sha256_text']}"
            possible[a["language"] + "/" + b["language"]].append((rank(seed, key), key, a, b))
    pairs, seen = [], set()
    for language_pair, choices in sorted(possible.items()):
        added = 0
        for _, key, a, b in sorted(choices, key=lambda choice: (choice[0], choice[1], choice[2]["source_id"])):
            if key in seen:
                reasons["duplicate_content_candidates_excluded"] += 1
                continue
            seen.add(key)
            pairs.append({**base_metadata("xlcost"), "pair_id": "XLC-CAND-" + digest(key.encode()),
                          "source_a": a["source_id"], "source_b": b["source_id"], "language": language_pair,
                          "code_sha256_text_a": a["code_sha256_text"], "code_sha256_text_b": b["code_sha256_text"],
                          "problem_id": None, "problem_title": a["problem_title"],
                          "problem_title_key": a["problem_title_key"], "public_label": None,
                          "upstream_split": "train", "relationship": "SAME_EXACT_TITLE_CANDIDATE_NOT_VERIFIED_PARALLEL_PAIR",
                          "alignment_basis": "unique_exact_problem_title_per_language_no_official_problem_id_in_mirror",
                          "representation": "tokenized_NOT_raw_source", "formal_blockers": ["missing_official_problem_map", "tokenized_source", "unreviewed_relationship", "unknown_author_family"]})
            added += 1
            if added == per_language_pair:
                break
    summary = {"source_records": len(sources),
               "source_records_by_language": dict(sorted(Counter(row["language"] for row in sources).items())),
               "sources_by_upstream_split": dict(sorted(Counter(row["upstream_split"] for row in sources).items())),
               "unique_language_text_hashes": len(hashes), "unique_problem_titles": len(titles),
               "source_records_without_alignment_title": sum(not row["problem_title"] for row in sources),
               "cross_split_language_text_hashes": sum(len(value) > 1 for value in hashes.values()),
               "selected_pairs": len(pairs),
               "candidate_pairs_by_language": dict(sorted(Counter(row["language"] for row in pairs).items())),
               "exclusions": dict(reasons), "formal_eligible_pairs": 0,
               "selection_uses_detector_scores": False, "problem_disjoint_verified": False,
               "source_disjoint_verified": False, "official_parallel_alignment_verified": False}
    return sorted(pairs, key=lambda row: row["pair_id"]), summary


def build(kind: str, upstream: Path, quota: int, seed: int):
    if kind == "poolc":
        path = upstream / "data/train-00000-of-00009.parquet"
        return poolc_select(lambda: poolc_rows(path), quota, seed)
    sources = xlcost_sources(upstream)
    pairs, summary = xlcost_candidates(sources, quota, seed)
    return sources, pairs, summary


def serialized_sources(sources: list[dict]):
    registry, codes = [], []
    for number, source in enumerate(sources, 1):
        registry.append({key: value for key, value in source.items() if key != "code"} |
                        {"code_path": "source_codes.jsonl", "code_line": number, "storage_format": "jsonl-row"})
        codes.append({"source_id": source["source_id"], "code": source["code"]})
    return registry, codes


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def intake(kind: str, cache: Path, output: Path, quota: int, seed: int, offline: bool):
    if output.exists():
        raise FileExistsError("Use a new intake directory; --verify-only does not overwrite")
    download(kind, cache, offline)
    sources, pairs, summary = build(kind, cache, quota, seed)
    registry, codes = serialized_sources(sources)
    output.mkdir(parents=True)
    for pin in PINS[kind]["files"]:
        target = output / "upstream" / pin["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cache / pin["path"], target)
    write_rows(output / "source_registry.jsonl", registry)
    write_rows(output / "source_codes.jsonl", codes)
    write_rows(output / "selected_pairs.jsonl", pairs)
    write_json(output / "audit_summary.json", summary)
    manifest = {"status": "EXTERNAL_EXPLORATORY_INTAKE_NOT_FORMAL_BENCHMARK", "dataset": kind,
                "source_repository": PINS[kind]["repository"], "source_revision": PINS[kind]["revision"],
                "pin_config_sha256": digest(PINS_PATH.read_bytes()), "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "random_seed": seed, "quota": quota, "summary": summary,
                "upstream_files": [{**pin, "observed_sha256": digest((cache / pin["path"]).read_bytes())} for pin in PINS[kind]["files"]],
                "registry_sha256": {name: digest((output / name).read_bytes()) for name in
                                    ("source_registry.jsonl", "source_codes.jsonl", "selected_pairs.jsonl", "audit_summary.json")},
                "license_observation": "PoolC dataset_infos.json has empty license; quarantine, no redistribution or formal metrics." if kind == "poolc" else
                    "HF mirror declares CC-BY-SA-4.0; upstream XLCoST repository Apache-2.0 does not automatically license original GeeksForGeeks sources. Preserve provenance; raw records remain local.",
                "detector_scored_pairs": 0, "formal_eligible_pairs": 0, "algorithm_changed": False,
                "all_downloaded_programs_executed": False}
    write_json(output / "manifest.json", manifest)
    return manifest


def verify(output: Path):
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    kind = manifest["dataset"]
    if kind not in PINS or manifest["source_revision"] != PINS[kind]["revision"] or manifest["pin_config_sha256"] != digest(PINS_PATH.read_bytes()):
        raise ValueError("Intake provenance or pin configuration changed")
    if manifest["formal_eligible_pairs"] != 0 or manifest["detector_scored_pairs"] != 0 or manifest["algorithm_changed"]:
        raise ValueError("Experimental boundary metadata changed")
    for pin in PINS[kind]["files"]:
        verify_pin(output / "upstream" / pin["path"], pin)
    expected_files = [{**pin, "observed_sha256": digest((output / "upstream" / pin["path"]).read_bytes())}
                      for pin in PINS[kind]["files"]]
    if manifest["upstream_files"] != expected_files or manifest["source_repository"] != PINS[kind]["repository"]:
        raise ValueError("Recorded upstream provenance changed")
    sources, pairs, summary = build(kind, output / "upstream", manifest["quota"], manifest["random_seed"])
    registry, codes = serialized_sources(sources)
    for name, expected in (("source_registry.jsonl", registry), ("source_codes.jsonl", codes), ("selected_pairs.jsonl", pairs)):
        if read_jsonl(output / name) != expected:
            raise ValueError(f"Intake content differs from pinned reconstruction: {name}")
    if json.loads((output / "audit_summary.json").read_text()) != json.loads(json.dumps(summary)) or manifest["summary"] != json.loads(json.dumps(summary)):
        raise ValueError("Reconstructed summary mismatch")
    for name, expected in manifest["registry_sha256"].items():
        path = (output / name).resolve()
        if not path.is_relative_to(output.resolve()) or digest(path.read_bytes()) != expected:
            raise ValueError("Unsafe or changed registry")
    return {"verified": True, "dataset": kind, "source_records": len(sources), "selected_pairs": len(pairs), "formal_eligible_pairs": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=sorted(PINS))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--pairs", type=int, default=30000, help="PoolC balanced total pairs")
    parser.add_argument("--per-language-pair", type=int, default=2000, help="XLCoST maximum candidates per language combination")
    parser.add_argument("--seed", type=int, default=20261010)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    output = (args.output or ROOT / f"data/public-datasets/{args.dataset}-20261010").resolve()
    cache = (args.cache or ROOT.parent / f".tmp/{args.dataset}-pinned").resolve()
    if args.verify_only:
        if json.loads((output / "manifest.json").read_text())["dataset"] != args.dataset:
            raise ValueError("Requested dataset differs from intake manifest")
        print(json.dumps(verify(output)))
    else:
        result = intake(args.dataset, cache, output, args.pairs if args.dataset == "poolc" else args.per_language_pair, args.seed, args.offline)
        print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
