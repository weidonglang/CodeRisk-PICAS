"""Research intake gates, independent of detector performance."""
import copy
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment"))

from add_research_v4_case import _parser, append_entry, build_entry
from research_v4_dataset import load_research_dataset, validate_cases
from research_v4_jplag import _exclusion_reason, align_with_picas, prepare_inputs


@pytest.fixture
def seed():
    manifest, cases, _ = load_research_dataset(ROOT / "experiment/datasets/research-v4/dataset.json")
    return manifest, copy.deepcopy(cases[0])


def verified_ai(case, case_type="AI_REWRITE"):
    case.update(source_type="ai_assisted", synthetic=False, data_origin="MANUAL",
                case_type=case_type, eligible_for_core_metrics=True)
    case["provenance"] = {
        "source": "self-authored unit fixture, not collected data",
        "license_or_authorization": "test fixture only", "model_name": "test-model",
        "prompt_template": "Rename identifiers", "generation_time": "2026-10-10T10:00:00+08:00",
        "manual_check_status": "VERIFIED", "functional_check_status": "PASSED",
    }
    return case


def test_placeholder_cannot_become_core_even_with_complete_ai_provenance(seed):
    manifest, case = seed
    verified_ai(case)
    case.update(source_type="placeholder", synthetic=True, data_origin="SYNTHETIC")
    report = validate_cases(manifest, [case])
    assert not report["valid"]
    assert any("placeholder cannot enter core metrics" in error for error in report["errors"])
    assert _exclusion_reason(case) == "PLACEHOLDER_NOT_ELIGIBLE"


@pytest.mark.parametrize("case_type", ["AI_REWRITE", "VARIABLE_RENAME"])
@pytest.mark.parametrize("field,value", [
    ("model_name", " "), ("prompt_template", ""), ("generation_time", None),
    ("generation_time", "yesterday"), ("generation_time", "2026-10-10T10:00:00"),
    ("manual_check_status", "PENDING"), ("functional_check_status", "FAILED"),
])
def test_ai_source_cannot_bypass_verification_with_other_case_type(seed, case_type, field, value):
    manifest, case = seed
    verified_ai(case, case_type)["provenance"][field] = value
    assert not validate_cases(manifest, [case])["valid"]
    assert _exclusion_reason(case) == "AI_PROVENANCE_NOT_VERIFIED"


@pytest.mark.parametrize("case_type", ["AI_REWRITE", "VARIABLE_RENAME"])
def test_verified_ai_same_language_is_jplag_eligible(seed, case_type):
    manifest, case = seed
    verified_ai(case, case_type)
    assert validate_cases(manifest, [case])["valid"]
    assert _exclusion_reason(case) is None
    case["eligible_for_core_metrics"] = False
    assert _exclusion_reason(case) == "NOT_ELIGIBLE_FOR_CORE_METRICS"


def intake_fixture(tmp_path):
    root = tmp_path / "dataset"
    (root / "pairs").mkdir(parents=True)
    (root / "samples").mkdir()
    (root / "samples/a.py").write_text("print(1)\n", encoding="utf-8")
    (root / "samples/b.py").write_text("print(2)\n", encoding="utf-8")
    shard = root / "pairs/manual_pairs.json"
    shard.write_text(json.dumps({"dataset_version": "unit-1", "cases": []}), encoding="utf-8")
    (root / "dataset.json").write_text(json.dumps({
        "dataset_version": "unit-1", "sources": [{"id": "manual-supplement",
        "format": "RESEARCH_V4_PAIRS_JSON", "path": "pairs/manual_pairs.json"}],
    }), encoding="utf-8")
    args = _parser().parse_args([
        "--pair-id", "UNIT-1", "--problem-id", "PROBLEM-1", "--problem-type", "simple_io",
        "--problem-group", "G1", "--dataset-split", "validation", "--source-id", "SOURCE-1",
        "--source-type", "synthetic", "--experiment-label", "TRANSFORMED",
        "--case-type", "VARIABLE_RENAME", "--language-a", "python", "--language-b", "python",
        "--code-a", "samples/a.py", "--code-b", "samples/b.py", "--dataset-version", "unit-1",
        "--title", "Unit fixture", "--description", "Self-authored workflow fixture",
        "--eligible-for-core-metrics",
    ])
    return root, shard, args


def test_helper_blocks_placeholder_and_blank_identifiers(tmp_path):
    root, _, args = intake_fixture(tmp_path)
    args.source_type = "placeholder"
    args.pair_id = " "
    entry, pending = build_entry(args, root)
    assert entry["eligible_for_core_metrics"] is False
    assert "pair_id" in pending
    assert "placeholder cannot enter core metrics" in pending


@pytest.mark.parametrize("leak", ["problem", "source", "hash", "version"])
def test_append_checks_entire_dataset_before_mutating_shard(tmp_path, leak):
    root, shard, args = intake_fixture(tmp_path)
    first, pending = build_entry(args, root)
    assert not pending
    append_entry(shard, first)
    before = shard.read_bytes()
    (root / "samples/c.py").write_text("print(3)\n", encoding="utf-8")
    (root / "samples/d.py").write_text("print(4)\n", encoding="utf-8")
    args.pair_id, args.problem_id, args.source_id = "UNIT-2", "PROBLEM-2", "SOURCE-2"
    args.dataset_split, args.code_a, args.code_b = "test", "samples/c.py", "samples/d.py"
    second, _ = build_entry(args, root)
    if leak == "problem":
        second["problem_id"] = first["problem_id"]
    elif leak == "source":
        second["source_id"] = first["source_id"]
    elif leak == "hash":
        second["code_a_path"], second["code_a_sha256"] = first["code_a_path"], first["code_a_sha256"]
    else:
        second["dataset_version"] = "other-version"
    with pytest.raises(ValueError):
        append_entry(shard, second)
    assert shard.read_bytes() == before


def test_verified_ai_aligns_through_manifest_loader(tmp_path):
    root, shard, args = intake_fixture(tmp_path)
    args.source_type, args.case_type = "ai_assisted", "AI_REWRITE"
    args.license_or_authorization = "unit fixture only"
    args.model_name, args.prompt_template = "unit-model", "Rename"
    args.generation_time = "2026-10-10T10:00:00+08:00"
    args.manual_check_status, args.functional_check_status = "VERIFIED", "PASSED"
    entry, pending = build_entry(args, root)
    assert not pending
    append_entry(shard, entry)
    result = prepare_inputs(root / "dataset.json", tmp_path / "jplag")
    assert [row["pairId"] for row in result["alignmentRows"]] == ["UNIT-1"]
    assert result["excludedRows"] == []


def test_helper_rejects_paths_outside_dataset(tmp_path):
    root, _, args = intake_fixture(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("print(0)", encoding="utf-8")
    args.code_a = str(outside)
    with pytest.raises(ValueError, match="escapes"):
        build_entry(args, root)


@pytest.mark.parametrize("field", ["source", "license_or_authorization"])
def test_non_synthetic_provenance_rejects_whitespace(seed, field):
    manifest, case = seed
    verified_ai(case)["provenance"][field] = " "
    assert not validate_cases(manifest, [case])["valid"]


def test_append_refuses_forged_hash_without_mutation(tmp_path):
    root, shard, args = intake_fixture(tmp_path)
    entry, _ = build_entry(args, root)
    entry["code_a_sha256"] = "sha256:" + "0" * 64
    before = shard.read_bytes()
    with pytest.raises(ValueError, match="hash"):
        append_entry(shard, entry)
    assert shard.read_bytes() == before


def test_hash_contract_normalizes_newlines(tmp_path):
    root, _, args = intake_fixture(tmp_path)
    (root / "samples/a.py").write_bytes(b"print(1)\r\n")
    (root / "samples/b.py").write_bytes(b"print(1)\n")
    entry, _ = build_entry(args, root)
    assert entry["code_a_sha256"] == entry["code_b_sha256"]


@pytest.mark.parametrize("mutation", ["hash", "split", "duplicate", "none", "legacy"])
def test_jplag_alignment_checks_prediction_identity(tmp_path, mutation):
    row = {"pairId": "UNIT-1", "problemId": "P1", "datasetSplit": "test",
           "experimentLabel": "TRANSFORMED", "caseType": "VARIABLE_RENAME",
           "language": "python", "sourceType": "synthetic",
           "codeASha256": "sha256:" + "a" * 64, "codeBSha256": "sha256:" + "b" * 64,
           "predictedScore": None, "resultStatus": "NO_NATIVE_COMPARISON"}
    prediction = {"pairId": "UNIT-1", "problemId": "P1", "split": "test", "label": "TRANSFORMED",
                  "codeASha256": row["codeASha256"], "codeBSha256": row["codeBSha256"]}
    if mutation == "hash":
        prediction["codeASha256"] = "sha256:" + "c" * 64
    elif mutation == "split":
        prediction["split"] = "validation"
    elif mutation == "legacy":
        prediction.pop("codeASha256")
        prediction.pop("codeBSha256")
    path = tmp_path / "predictions.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(prediction))
        writer.writeheader()
        writer.writerow(prediction)
        if mutation == "duplicate":
            writer.writerow(prediction)
    if mutation in {"hash", "split", "duplicate"}:
        with pytest.raises(ValueError):
            align_with_picas([row], path)
    else:
        result = align_with_picas([row], path)[0]
        assert result["sourceHashesVerified"] is (mutation != "legacy")
        assert result["jplagScore"] is None
