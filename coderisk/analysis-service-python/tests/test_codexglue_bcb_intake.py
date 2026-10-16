"""Self-authored intake fixtures; no public-data labels or algorithm scores are produced."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment"))
from acquire_codexglue_bcb import audit_and_select, fetch_pinned, iter_pairs, load_functions, pair_index, verify_blob
import acquire_codexglue_bcb as intake_module


def fixture_inputs(tmp_path):
    rows = [{"idx": str(i), "func": f"int value() {{ return {i}; }}"} for i in range(1, 7)]
    rows[4]["func"] = rows[0]["func"]
    (tmp_path / "data.jsonl").write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    (tmp_path / "train.txt").write_text(
        "1 2 1\n2 1 1\n2 3 1\n3 4 1\n1 5 1\n1 3 0\n1 4 0\n2 4 0\n4 6 0\n", encoding="utf-8")
    (tmp_path / "valid.txt").write_text("1 3 1\n2 6 0\n", encoding="utf-8")
    (tmp_path / "test.txt").write_text("1 2 1\n3 6 0\n", encoding="utf-8")
    return load_functions(tmp_path / "data.jsonl")


def test_balanced_selection_deduplicates_and_quarantines_conflicting_labels(tmp_path):
    sources = fixture_inputs(tmp_path)
    report, rows = audit_and_select(tmp_path, sources, target=4, seed=7)
    assert len(rows) == 4
    assert report["selected_labels"] == {0: 2, 1: 2}
    assert report["selected_distinct_text_pairs"] == 4
    assert report["conflicting_text_pair_labels_quarantined"] == 1
    assert report["upstream_split_counts"]["train"]["duplicate_or_reversed_text_pair_rows"] == 1
    assert report["upstream_split_counts"]["train"]["identical_text_rows_excluded"] == 1
    assert all({row["source_a"], row["source_b"]} != {"BCB-SRC-1", "BCB-SRC-3"} for row in rows)
    assert all(row["experiment_label"] == "UNCERTAIN" and not row["eligible_for_core_metrics"] for row in rows)
    assert all(row["upstream_split"] == "train" and row["dataset_split"] == "development" for row in rows)
    assert all(row["problem_id"] is None for row in rows)


def test_selection_is_deterministic_without_detector_scores(tmp_path):
    sources = fixture_inputs(tmp_path)
    first = audit_and_select(tmp_path, sources, target=4, seed=7)
    assert audit_and_select(tmp_path, sources, target=4, seed=7) == first
    assert first[0]["selection_uses_detector_scores"] is False


def test_split_overlap_is_disclosed_not_claimed_disjoint(tmp_path):
    sources = fixture_inputs(tmp_path)
    report, _ = audit_and_select(tmp_path, sources, target=4, seed=7)
    assert report["text_pairs_in_multiple_upstream_splits"] == 2
    assert any(row["shared_function_ids"] > 0 for row in report["upstream_source_overlap"])
    assert report["problem_disjoint_verified"] is False
    assert report["formal_eligible_pairs"] == 0


def test_compact_pair_index_has_no_collisions():
    size = 15
    keys = {pair_index(a, b, size) for a in range(size) for b in range(a + 1, size)}
    assert keys == set(range(size * (size - 1) // 2))
    assert pair_index(2, 8, size) == pair_index(8, 2, size)


@pytest.mark.parametrize("line", ["1 99 0", "1 2 7", "1 2", "1 2 0 extra"])
def test_missing_reference_or_invalid_pair_fails_closed(tmp_path, line):
    sources = fixture_inputs(tmp_path)
    (tmp_path / "broken.txt").write_text(line, encoding="utf-8")
    with pytest.raises(ValueError):
        list(iter_pairs(tmp_path / "broken.txt", sources))


def test_duplicate_function_idx_and_unsafe_identifier_rejected(tmp_path):
    for idx in ("1", "../escape"):
        rows = [{"idx": "1", "func": "int a(){return 1;}"}, {"idx": idx, "func": "int b(){return 2;}"}]
        path = tmp_path / "sources.jsonl"
        path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
        with pytest.raises(ValueError):
            load_functions(path)


def test_unavailable_balanced_quota_is_not_fabricated(tmp_path):
    sources = fixture_inputs(tmp_path)
    with pytest.raises(ValueError, match="Insufficient"):
        audit_and_select(tmp_path, sources, target=20, seed=7)


def test_pinned_blob_checks_size_and_content():
    data = b"unit fixture"
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    verify_blob(data, len(data), blob)
    with pytest.raises(ValueError):
        verify_blob(data + b"x", len(data), blob)


def test_offline_missing_cache_does_not_download(tmp_path):
    with pytest.raises(FileNotFoundError):
        fetch_pinned(tmp_path, "data.jsonl", offline=True)


@pytest.mark.parametrize("tamper", ["none", "source", "pair"])
def test_offline_reconstruction_verifies_intake_and_rejects_tampering(tmp_path, monkeypatch, tamper):
    cache = tmp_path / "cache"
    cache.mkdir()
    fixture_inputs(cache)
    pins = {}
    for name in ("data.jsonl", "train.txt", "valid.txt", "test.txt"):
        data = (cache / name).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        pins[name] = (name, len(data), blob)
    monkeypatch.setattr(intake_module, "PINS", pins)
    monkeypatch.setattr(intake_module, "EXPECTED_ROWS", {"train": 9, "valid": 2, "test": 2})
    output = tmp_path / "output"
    intake_module.intake(cache, output, target=4, seed=7, offline=True)
    if tamper == "none":
        assert intake_module.verify(output)["selected_pairs"] == 4
        with pytest.raises(FileExistsError):
            intake_module.intake(cache, output, target=4, seed=7, offline=True)
    else:
        if tamper == "source":
            (output / "sources/1.java").write_text("changed", encoding="utf-8")
        else:
            path = output / "selected_pairs.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            rows[0]["published_label"] = 1 - rows[0]["published_label"]
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
        with pytest.raises(ValueError):
            intake_module.verify(output)
