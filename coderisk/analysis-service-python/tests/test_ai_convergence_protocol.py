from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiment"))
from ai_convergence.examples.make_seed import make_seed
from ai_convergence.protocol import Corpus, digest, safe_file, export_schemas
from ai_convergence.validate import validate
from ai_convergence.ingest import ingest
from ai_convergence.build_pairs import build, relation_reasons


@pytest.fixture
def source(tmp_path):
    return make_seed(tmp_path / "source")


def edit(source, change):
    data = json.loads(source.read_text(encoding="utf-8"))
    change(data)
    source.write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize("path", ["../outside.py", "/etc/passwd", "C:/secret.py", "C:\\secret.py",
    "https://host/private", "//server/share", "code/../../private", "", "code\\file.py"])
def test_paths_cannot_read_outside_root(source, path):
    with pytest.raises(ValueError):
        safe_file(source.parent, path)


def test_mock_import_is_explicitly_development_only(source, tmp_path):
    _, _, report = validate(source)
    assert (report["sample_count"], report["session_count"], report["synthetic_count"]) == (13, 12, 13)
    assert report["status"] == "DEVELOPMENT_ONLY"
    assert report["network_calls"] == report["code_executions"] == 0
    target = tmp_path / "snapshot"
    ingest(source, target)
    assert validate(target / "corpus.json")[2]["file_sha256"] == report["file_sha256"]
    with pytest.raises(FileExistsError):
        ingest(source, target)


def test_dry_run_never_creates_output(source, tmp_path):
    target = tmp_path / "not-written"
    ingest(source, target, dry_run=True)
    assert not target.exists()


@pytest.mark.parametrize("change", [
    lambda d: d["artifacts"][0].pop("license_or_authorization_ref"),
    lambda d: d["artifacts"][0].update(code_sha256="0" * 64),
    lambda d: d["questions"][0].update(question_text_sha256="0" * 64),
    lambda d: d["sessions"][0].update(prompt_sha256="0" * 64),
    lambda d: d["sessions"].append(d["sessions"][0]),
    lambda d: d["artifacts"].append(d["artifacts"][0]),
    lambda d: d["sessions"][0].update(generation_time_utc="2026-10-12T12:00:00"),
    lambda d: d["sessions"][0].update(temperature=float("nan")),
    lambda d: d["artifacts"][0].update(origin_type="AI", generation_session_id=None),
    lambda d: d["pair_relations"][0].update(claimed_relation="CHEATING"),
    lambda d: d["pair_relations"][0].update(review_status="AGREED"),
    lambda d: d["artifacts"][0].update(functional_check_status="PASSED"),
    lambda d: d["artifacts"][0].update(synthetic=False),
])
def test_metadata_pollution_is_rejected(source, change):
    edit(source, change)
    with pytest.raises(ValueError):
        validate(source)


def test_unknown_extra_secret_is_not_echoed(source):
    edit(source, lambda d: d.update(api_key="PRIVATE-DO-NOT-ECHO"))
    with pytest.raises(ValueError) as error:
        validate(source)
    assert "PRIVATE-DO-NOT-ECHO" not in str(error.value)


@pytest.mark.parametrize("dimension", ["source_family_id", "code", "problem_family"])
def test_connected_split_leakage_is_rejected(source, dimension):
    data = json.loads(source.read_text(encoding="utf-8"))
    a, b = data["artifacts"][0], data["artifacts"][4]
    if dimension == "source_family_id":
        b[dimension] = a[dimension]
        data["sessions"][4][dimension] = a[dimension]
    elif dimension == "problem_family":
        data["questions"][1][dimension] = data["questions"][0][dimension]
    else:
        code = (source.parent / a["code_path"]).read_bytes()
        (source.parent / b["code_path"]).write_bytes(code)
        b["code_sha256"] = digest(code)
    source.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="leakage"):
        validate(source)


def test_repeated_prompt_family_is_disclosed_not_silently_claimed_disjoint(source):
    report = validate(source)[2]
    assert report["sensitivity"]["prompt_family"]["cross_split_values"] == 1
    assert "NOT_MODEL_DISJOINT" in report["sensitivity"]["model_version_or_snapshot"]["status"]


def test_duplicate_session_capture_rejected(source):
    edit(source, lambda d: d["sessions"][1].update(session_record_ref=d["sessions"][0]["session_record_ref"]))
    with pytest.raises(ValueError, match="Duplicated"):
        validate(source)


def test_same_code_in_distinct_mock_models_is_kept_without_false_label(source, tmp_path):
    manifest, index = build(source, tmp_path / "pairs")
    assert len(index) == 22 and manifest["status"] == "DEVELOPMENT_ONLY"
    cases = json.loads((tmp_path / "pairs/pairs.json").read_text(encoding="utf-8"))["cases"]
    assert all(c["experiment_label"] == "UNCERTAIN" and not c["eligible_for_core_metrics"] for c in cases)
    row = next(r for r in index if r["sample_a"] == "MOCK-sum-0" and r["sample_b"] == "MOCK-sum-2")
    assert row["claimed_relation"] == "AI_INDEPENDENT_CROSS_MODEL" and row["resolved_relation"] == "UNCERTAIN"
    assert any("Synthetic" in reason for reason in row["reasons"])


def test_pair_cap_does_not_silently_select_easy_cases(source, tmp_path):
    with pytest.raises(ValueError, match="cap"):
        build(source, tmp_path / "pairs", max_pairs=1)
    assert not (tmp_path / "pairs").exists()


def test_source_capture_mismatch_rejected(source):
    edit(source, lambda d: d["sessions"][0].update(model_id="OTHER"))
    with pytest.raises(ValueError, match="contradicts"):
        validate(source)


def test_schemas_follow_executable_models(tmp_path):
    export_schemas(tmp_path / "schemas")
    schema = json.loads((tmp_path / "schemas/corpus.schema.json").read_text())
    assert schema == Corpus.model_json_schema() and schema["additionalProperties"] is False


def test_parent_cycle_rejected(source):
    edit(source, lambda d: (d["artifacts"][0].update(parent_sample_id=d["artifacts"][1]["sample_id"]),
                           d["artifacts"][1].update(parent_sample_id=d["artifacts"][0]["sample_id"])))
    with pytest.raises(ValueError, match="cycle"):
        validate(source)


def test_reserved_import_file_cannot_overwrite_snapshot(source, tmp_path):
    data = json.loads(source.read_text(encoding="utf-8"))
    data["questions"][0]["question_path"] = "ingest_report.json"
    content = b"Untrusted imported bytes"
    (source.parent / "ingest_report.json").write_bytes(content)
    data["questions"][0]["question_text_sha256"] = digest(content)
    source.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="reserved"):
        ingest(source, tmp_path / "safe")
    assert not (tmp_path / "safe").exists()


def test_changed_raw_response_cannot_keep_a_valid_session_record(source):
    data = json.loads(source.read_text(encoding="utf-8"))
    ref = data["artifacts"][0]["raw_output_ref"]
    (source.parent / ref).write_bytes(b"Substituted unrecorded output")
    with pytest.raises(ValueError, match="Raw output hash"):
        validate(source)


def test_failed_generation_requires_evidence(source):
    edit(source, lambda d: d["sessions"][0].update(attempt_status="FAILED"))
    with pytest.raises(ValueError, match="failure reference"):
        validate(source)


def test_functional_failure_does_not_change_a_process_relationship(source):
    corpus = validate(source)[0]
    a, b = corpus.artifacts[:2]
    a = a.model_copy(update={"synthetic": False, "origin_type": "HUMAN", "ai_assistance_type": "HUMAN_ONLY", "parent_sample_id": b.sample_id})
    b = b.model_copy(update={"synthetic": False, "origin_type": "HUMAN", "ai_assistance_type": "HUMAN_ONLY"})
    relation = corpus.pair_relations[0].model_copy(update={"claimed_relation": "KNOWN_DERIVED_HUMAN", "review_status": "AGREED"})
    # In-memory UNIT_TEST_ONLY declarations test the separation, not genuine reviewer identities.
    assert relation_reasons(relation, a, b, {}) == []


def test_independent_pair_in_one_session_is_not_certified(source):
    corpus = validate(source)[0]
    a, b = corpus.artifacts[:2]
    a = a.model_copy(update={"synthetic": False})
    b = b.model_copy(update={"synthetic": False, "generation_session_id": a.generation_session_id})
    relation = corpus.pair_relations[0].model_copy(update={"claimed_relation": "AI_INDEPENDENT_SAME_MODEL", "review_status": "AGREED"})
    reasons = relation_reasons(relation, a, b, {s.generation_session_id: s for s in corpus.sessions})
    assert any("Separate AI session" in reason for reason in reasons)


def test_committed_schemas_match_current_executable_protocol():
    root = Path(__file__).resolve().parents[2] / "experiment/ai_convergence/schema"
    assert json.loads((root / "corpus.schema.json").read_text(encoding="utf-8")) == Corpus.model_json_schema()


def test_failed_function_check_remains_a_descriptive_artifact(source, tmp_path):
    (source.parent / "function-failure.txt").write_text("UNIT_TEST_ONLY: declared failed check, no execution", encoding="utf-8")
    edit(source, lambda d: d["artifacts"][0].update(functional_check_status="FAILED", functional_check_evidence="function-failure.txt"))
    assert validate(source)[0].artifacts[0].functional_check_status == "FAILED"
    _, pairs = build(source, tmp_path / "pairs")
    assert len(pairs) == 22


def test_nonhuman_reviewers_cannot_satisfy_real_review_gate(source):
    data = json.loads(source.read_text(encoding="utf-8"))
    a, b = data["artifacts"][0], data["artifacts"][2]
    data["pair_relations"][0].update(review_status="AGREED", reviewer_ids=["UNIT-AI-A", "UNIT-AI-B"],
        reviewer_types=["AI", "AI"], reviewer_independence_confirmed=True,
        reviewed_code_sha256=[a["code_sha256"], b["code_sha256"]], label_evidence_ref="SYNTHETIC_NOTICE.txt",
        reviewed_at="2026-10-12T00:00:00Z")
    source.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="HUMAN"):
        validate(source)
