"""Self-authored small fixtures; no downloaded programs are executed."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment"))
import acquire_nonjava_datasets as intake
from record_nonjava_intake_evidence import summarize


def python_row(a, b, label, group_a=1, group_b=2):
    return {"code1": a, "code2": b, "similar": label, "pair_id": None,
            "question_pair_id": None, "code1_group": group_a, "code2_group": group_b}


def python_fixture():
    a, b, c, d = [f"print({n})\n" for n in range(4)]
    return [python_row(a, b, 1), python_row(b, a, 1), python_row(b, c, 1),
            python_row(a, c, 0), python_row(c, a, 1), python_row(a, d, 0),
            python_row(b, d, 0), python_row(a, a, 1), python_row("", c, 0)]


def test_python_dedup_and_conflict_quarantine():
    sources, pairs, report = intake.poolc_select(lambda: iter(python_fixture()), 4, 7)
    assert report["selected_pairs"] == 4
    assert report["selected_labels"] == {0: 2, 1: 2}
    assert report["conflicting_text_pair_labels_quarantined"] == 1
    assert report["duplicate_or_reversed_text_pair_rows"] == 2
    assert report["identical_text_rows_excluded"] == 1
    assert report["invalid_or_oversized_code_rows_excluded"] == 1
    assert all(row["experiment_label"] == "UNCERTAIN" for row in pairs)
    assert all(row["problem_id"] is None and not row["eligible_for_core_metrics"] for row in sources + pairs)
    assert all(row["license_status"].startswith("UNSPECIFIED") for row in pairs)


def test_python_determinism_and_no_detector_scores():
    first = intake.poolc_select(lambda: iter(python_fixture()), 4, 9)
    assert first == intake.poolc_select(lambda: iter(python_fixture()), 4, 9)
    assert first[2]["selection_uses_detector_scores"] is False
    assert first[2]["validation_test_hash_isolation_verified"] is False


@pytest.mark.parametrize("quota", [0, 1, 3, 10])
def test_python_quota_not_filled_by_fabrication(quota):
    with pytest.raises(ValueError):
        intake.poolc_select(lambda: iter(python_fixture()), quota, 0)


@pytest.mark.parametrize("label", [2, None, True, "1"])
def test_python_bad_label_fails_closed(label):
    with pytest.raises(ValueError, match="publisher label"):
        intake.poolc_select(lambda: iter([python_row("a=1", "b=2", label)]), 2, 0)


def test_python2_parser_fallback_is_disclosed_not_converted():
    rows = [python_row("print 1", "print(2)", 1), python_row("print(3)", "print(4)", 0)]
    sources, _, report = intake.poolc_select(lambda: iter(rows), 2, 0)
    assert any(row["syntax_status"].startswith("PYTHON3_PARSE_FAILED") for row in sources)
    assert report["selected_source_syntax"]["PYTHON3_PARSE_FAILED_POSSIBLE_PYTHON2_OR_UNSUPPORTED"] == 1
    assert any(row["code"] == "print 1" for row in sources)


def token_source(sid, language, title, split="train", code=None):
    code = code or f"{language} {sid} NEW_LINE"
    return {"source_id": sid, "language": language, "upstream_split": split,
            "problem_title": title, "problem_title_key": intake.digest(title.encode()),
            "code_sha256_text": intake.code_hash(code), "code": code}


def test_title_candidates_skip_split_leakage_and_ambiguous_titles():
    rows = [token_source("p1", "python", "unique"), token_source("c1", "c", "unique"),
            token_source("p2", "python", "ambiguous"), token_source("p3", "python", "ambiguous"),
            token_source("c2", "c", "ambiguous"), token_source("p4", "python", "leak"),
            token_source("c4", "c", "leak", "test")]
    pairs, summary = intake.xlcost_candidates(rows, 2000, 0)
    assert len(pairs) == 1
    assert pairs[0]["language"] == "c/python"
    assert pairs[0]["public_label"] is None and not pairs[0]["eligible_for_core_metrics"]
    assert "NOT_VERIFIED_PARALLEL_PAIR" in pairs[0]["relationship"]
    assert summary["exclusions"]["titles_across_upstream_splits_excluded"] == 1
    assert summary["exclusions"]["ambiguous_same_language_titles_excluded"] == 1


def test_cross_split_code_hash_reuse_excludes_otherwise_unique_title():
    rows = [token_source("p1", "python", "one", code="reused"), token_source("c1", "c", "one"),
            token_source("p2", "python", "other", "valid", code="reused")]
    pairs, report = intake.xlcost_candidates(rows, 2, 0)
    assert not pairs
    assert report["cross_split_language_text_hashes"] == 1


def test_content_identical_and_duplicate_cross_language_pairs_not_counted_twice():
    rows = [token_source("p1", "python", "one", code="same"), token_source("c1", "c", "one", code="same"),
            token_source("p2", "python", "two", code="py"), token_source("c2", "c", "two", code="c"),
            token_source("p3", "python", "three", code="py"), token_source("c3", "c", "three", code="c")]
    pairs, report = intake.xlcost_candidates(rows, 9, 0)
    assert len(pairs) == 1
    assert report["exclusions"]["identical_cross_language_token_text_excluded"] == 1
    assert report["exclusions"]["duplicate_content_candidates_excluded"] == 1


def test_language_quotas_and_stable_selection():
    rows = [token_source(f"{lang}{n}", lang, f"problem{n}") for n in range(5) for lang in ("cpp", "python", "javascript")]
    first = intake.xlcost_candidates(rows, 2, 99)
    assert len(first[0]) == 6
    assert set(first[1]["candidate_pairs_by_language"].values()) == {2}
    assert first == intake.xlcost_candidates(list(reversed(rows)), 2, 99)
    with pytest.raises(ValueError):
        intake.xlcost_candidates(rows, 0, 0)


def test_tokenized_inputs_are_preserved_not_masquerading_as_source(tmp_path):
    for language in intake.LANGUAGES:
        folder = tmp_path / "data" / f"{language}-program-level"
        folder.mkdir(parents=True)
        for split in ("train", "valid", "test"):
            (folder / f"{split}.json").write_text(json.dumps({"text": f"title-{split} | comment", "code": "x NEW_LINE INDENT y DEDENT"}) + "\n")
    sources = intake.xlcost_sources(tmp_path)
    assert len(sources) == 21
    assert all("NOT_RAW_SOURCE" in row["representation"] for row in sources)
    registry, codes = intake.serialized_sources(sources)
    assert registry[0]["code_line"] == 1
    assert "code" not in registry[0] and codes[0]["code"] == "x NEW_LINE INDENT y DEDENT"


def test_trailing_title_separator_and_missing_title_are_handled_without_guessing(tmp_path):
    for language in intake.LANGUAGES:
        folder = tmp_path / "data" / f"{language}-program-level"
        folder.mkdir(parents=True)
        for split in ("train", "valid", "test"):
            text = "title |" if split == "train" else "no publisher separator"
            (folder / f"{split}.json").write_text(json.dumps({"text": text, "code": f"{language} {split}"}) + "\n")
    sources = intake.xlcost_sources(tmp_path)
    pairs, summary = intake.xlcost_candidates(sources, 2, 9)
    assert summary["source_records_without_alignment_title"] == 14
    assert summary["selected_pairs"] == 21
    assert all(row["problem_title"] == "title" for row in pairs)


def test_pinned_checks_and_offline_cache(tmp_path):
    path = tmp_path / "raw.bin"
    path.write_bytes(b"fixture")
    pin = {"path": "raw.bin", "size": 7, "sha256": intake.digest(b"fixture")}
    intake.verify_pin(path, pin)
    pin["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        intake.verify_pin(path, pin)
    with pytest.raises(FileNotFoundError):
        intake.download("poolc", tmp_path, True)


@pytest.mark.parametrize("tamper", [None, "pair", "source", "provenance"])
def test_intake_verification_reconstructs_from_pinned_files(tmp_path, monkeypatch, tamper):
    # Test the whole local path with a tiny self-authored replacement for the network pin set.
    cache = tmp_path / "cache"
    cache.mkdir()
    raw = b"self-authored fixture"
    (cache / "fixture.bin").write_bytes(raw)
    monkeypatch.setitem(intake.PINS, "poolc", {"repository": "fixture/local", "revision": "fixture-revision",
                                              "files": [{"path": "fixture.bin", "size": len(raw), "sha256": intake.digest(raw)}]})
    sources, pairs, summary = intake.poolc_select(lambda: iter(python_fixture()), 4, 7)
    monkeypatch.setattr(intake, "build", lambda *_: (sources, pairs, summary))
    output = tmp_path / "intake"
    intake.intake("poolc", cache, output, 4, 7, True)
    assert intake.verify(output)["selected_pairs"] == 4
    with pytest.raises(FileExistsError):
        intake.intake("poolc", cache, output, 4, 7, True)
    if tamper:
        filename = {"pair": "selected_pairs.jsonl", "source": "source_codes.jsonl", "provenance": "manifest.json"}[tamper]
        path = output / filename
        if tamper == "provenance":
            value = json.loads(path.read_text())
            value["upstream_files"][0]["observed_sha256"] = "0" * 64
            path.write_text(json.dumps(value))
        else:
            path.write_text(path.read_text().replace("POOLC", "TAMPERED"))
        with pytest.raises(ValueError):
            intake.verify(output)


def test_pin_schema_contains_seven_languages_and_bounded_shard():
    assert len(intake.PINS["xlcost"]["files"]) == 22
    assert len(intake.PINS["poolc"]["files"]) == 2
    for dataset in intake.PINS.values():
        assert len(dataset["revision"]) == 40
        for pin in dataset["files"]:
            assert len(pin.get("sha256", pin.get("git_blob"))) in (40, 64)


def test_evidence_counts_javascript_as_nonjava_and_separates_tokenized_sources():
    sources, pairs, _ = intake.poolc_select(lambda: iter(python_fixture()), 4, 7)
    token_sources = [token_source("p", "python", "x"), token_source("j", "javascript", "x"), token_source("v", "java", "x")]
    candidates, _ = intake.xlcost_candidates(token_sources, 1, 0)
    report = summarize({"poolc": sources, "xlcost": token_sources}, {"poolc": pairs, "xlcost": candidates})
    assert report["raw_python_published_pairs"] == 4
    assert report["tokenized_program_records"] == 3
    assert report["xlcost_candidates_without_java"] == 1
    assert report["registered_pair_rows"] == 7
    assert report["eligible_for_core_metrics"] == report["synthetic_pairs"] == report["placeholder_pairs"] == 0
