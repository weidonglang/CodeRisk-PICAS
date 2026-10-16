from pathlib import Path
import json
import sys
import subprocess

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiment"))
from ai_convergence.examples.make_seed import make_seed
from ai_convergence.analyze import run
from ai_convergence.descriptive_stats import distribution, paired_cluster_interval
from ai_convergence.context import evidence_card, reference_summary
from ai_convergence.jplag import prepare, validate_baseline
from ai_convergence.prepare_review import prepare as prepare_review
from ai_convergence.protocol import digest
from ai_convergence.export_public import export
from ai_convergence.analyze import metrics_by_relation
from run_fair_evaluation import write_csv
from run_research_v4 import _request
from app.analyzers.token_similarity import analyze_token_pair


@pytest.fixture(scope="module")
def experiment(tmp_path_factory):
    root = tmp_path_factory.mktemp("offline-convergence")
    source = make_seed(root / "source")
    manifest = run(source, root / "run")
    return root, source, manifest


def test_actual_offline_mock_pipeline_never_reports_formal_accuracy(experiment):
    root, _, manifest = experiment
    assert manifest["status"] == "DEVELOPMENT_ONLY" and manifest["pair_count"] == 22
    assert manifest["formal_eligible_pairs"] == manifest["network_calls"] == manifest["code_executions"] == 0
    result = json.loads((root / "run/results.json").read_text(encoding="utf-8"))
    assert all(row["f1"] is None and row["fpr"] is None for row in result["evaluation"]["metrics"])
    assert result["baseline"]["status"] == "NOT_RUN"
    assert result["cluster"]["status"] == "NOT_ESTIMABLE_TOO_FEW_CONNECTED_CLUSTERS"


def test_missing_and_fallback_samples_are_not_deleted(experiment):
    root, _, _ = experiment
    rows = json.loads((root / "run/results.json").read_text(encoding="utf-8"))["rows"]
    assert len(rows) == 22 and any(row["canonical"] is None for row in rows)
    assert any("JAVA_HEADER_SHADOW" in row["warnings"] for row in rows)
    assert any("syntax" in row["warnings"].lower() or "parse" in row["warnings"].lower() for row in rows)


def test_full_sequence_and_fingerprint_equality_report_denominators(experiment):
    root, _, _ = experiment
    rows = json.loads((root / "run/results.json").read_text(encoding="utf-8"))["rows"]
    rename = next(row for row in rows if {row["sample_a"], row["sample_b"]} == {"MOCK-sum-0", "MOCK-sum-controlled-rename"})
    assert rename["complete_c_equal"] and rename["ngram_set_equal"]
    assert rename["canonical"] == 1 and rename["raw"] < 1
    assert all(row["gold_orbit_relation"] == "UNKNOWN_NOT_INFERRED_FROM_SCORES" for row in rows)


def test_context_is_read_only_template_and_short_code_are_visible(experiment):
    root, _, _ = experiment
    cards = json.loads((root / "run/context_evidence.json").read_text(encoding="utf-8"))
    assert all(not card["production_score_changed"] and not card["relationship_determined"] for card in cards)
    assert all(card["ai_reference_mode"] == "DEVELOPMENT_ONLY" and card["independent_reference_pool_size"] == 0 for card in cards)
    assert any(0 in card["effective_code_length"].values() for card in cards)
    assert any("SHARED_TEMPLATE_DOMINATES" in card["assessment"].get("reasons", []) for card in cards)
    assert all(card["match_length_distribution"]["status"] == "UNAVAILABLE" for card in cards)
    assert all("tokens" not in position for card in cards for position in card["match_locations"])


def test_no_reference_does_not_invent_patterns(experiment):
    root, _, _ = experiment
    card = json.loads((root / "run/context_evidence.json").read_text(encoding="utf-8"))[0]
    absent = reference_summary("none", [], {}, {})
    assert absent["mode"] == "UNAVAILABLE" and absent["unique_forms"] is None
    assert "没有可用" in absent["message"]


def test_two_worlds_identical_observations_have_identical_output():
    case = {"question": {"title": "Same observed problem", "description": "Add two integers."},
            "language_a": "python", "language_b": "python", "code_a": "a,b=map(int,input().split())\nprint(a+b)",
            "code_b": "a,b=map(int,input().split())\nprint(a+b)"}
    # Histories deliberately never enter the source-only production request.
    outputs = [analyze_token_pair(_request(1, case, "PICAS_STANDARD")).model_dump()
               for history in ("INDEPENDENT_WORLD", "COPY_WORLD")]
    assert outputs[0] == outputs[1]


def test_formal_run_actually_blocks_seed_and_saves_reasons(tmp_path):
    source = make_seed(tmp_path / "source")
    result = run(source, tmp_path / "formal", formal=True)
    assert result["status"] == "FORMAL_BLOCKED" and result["exit_code"] == 2
    assert (tmp_path / "formal/FORMAL_BLOCKED.json").is_file()
    assert not (tmp_path / "formal/metrics.csv").exists()


def test_prior_run_cannot_be_overwritten(experiment):
    root, source, _ = experiment
    before = (root / "run/run_manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        run(source, root / "run")
    assert (root / "run/run_manifest.json").read_bytes() == before


@pytest.mark.parametrize("values", [[], [None], [None, .25], [.25, .75]])
def test_quantiles_and_missing_denominators(values):
    result = distribution(values, len(values))
    assert result["n_available"] + result["n_missing"] == len(values)
    if not any(v is not None for v in values):
        assert result["p95"] is None


def test_cluster_bootstrap_is_macro_paired_reproducible_not_pair_weighted():
    rows = [{"group_id": "A", "raw": .2, "canonical": .8}] * 100 + [{"group_id": "B", "raw": .8, "canonical": .2}]
    kwargs = dict(seed=19, replicates=100, minimum_clusters=2)
    first = paired_cluster_interval(rows, **kwargs)
    assert first == paired_cluster_interval(list(reversed(rows)), **kwargs)
    assert first["clusters"] == 2 and abs(first["point"]) < 1e-12 and not first["pair_bootstrap"]


def test_no_native_baseline_is_ever_filled_with_zero(experiment, tmp_path):
    root, _, _ = experiment
    result = prepare(root / "run/dataset/dataset.json", tmp_path / "native")
    assert result["status"] == "NOT_RUN_PREPARED"
    assert len(result["excluded_pairs"]) > 0
    with pytest.raises(ValueError, match="not completed"):
        config = json.loads((root / "run/config.json").read_text(encoding="utf-8"))
        validate_baseline(tmp_path / "native", root / "run/dataset/dataset.json", [], config, False)


def test_review_queue_is_unknown_and_no_humans_are_invented(experiment, tmp_path):
    root, source, _ = experiment
    result = prepare_review(source, root / "run/dataset/dataset.json", tmp_path / "review")
    assert result["human_reviews"] == result["study_participants"] == 0
    queue = [json.loads(line) for line in (tmp_path / "review/blind_batch.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(queue) == 22 and all(r["experiment_label"] == "UNCERTAIN" for r in queue)
    html = (tmp_path / "review/workbench.html").read_text(encoding="utf-8")
    assert "MOCK-MODEL" not in html and "MOCK-SNAPSHOT" not in html


def test_report_has_both_workflows_without_behavioral_verdict(experiment):
    root, _, _ = experiment
    for name in ("REPORT.md", "assignment_preflight.md", "submission_review.md"):
        text = (root / "run" / name).read_text(encoding="utf-8")
        assert text and all(term not in text for term in ("确认抄袭", "作弊成立", "使用了ChatGPT"))


def test_public_export_never_contains_source_code_session_or_private_paths(experiment, tmp_path):
    root, _, _ = experiment
    report = export(root / "run", tmp_path / "public")
    content = ''.join(p.read_text(encoding="utf-8") for p in (tmp_path / "public").iterdir())
    assert not report["raw_code_included"] and not report["publication_authorized_by_tool"]
    assert all(value not in content for value in ("def fold", "class Main", "SESSION", str(root), "MOCK-sum"))
    with pytest.raises(ValueError):
        export(root / "run", tmp_path / "small", minimum_cell_size=1)


def test_ai_fpr_requires_trusted_relationship_denominator():
    config = {"methods": [{"name": "RAW_ONLY"}]}
    row = {"pair_id": "UNIT-TEST-ONLY", "split": "test", "resolved_relation": "AI_INDEPENDENT_CROSS_MODEL", "label": "INDEPENDENT"}
    evaluation = {"predictions": [{"method": "RAW_ONLY", "pair_id": row["pair_id"], "in_common_support": True, "predicted": True}]}
    measured = metrics_by_relation([row], evaluation, config, True)
    group = next(r for r in measured if r["relation"] == row["resolved_relation"])
    assert group["FPR_independent_AI"] == 1 and group["n_trusted"] == 1
    missing = metrics_by_relation([], {"predictions": []}, config, False)
    assert all(r["FPR_independent_AI"] is None for r in missing)


def test_two_world_context_with_absent_pool_never_invents_source_claim(experiment):
    root, _, _ = experiment
    row = json.loads((root / "run/results.json").read_text(encoding="utf-8"))["rows"][0]
    case = {"question": {"title": "Mock", "description": "Code only."}, "language_a": "python", "language_b": "python",
            "code_a": "print(1)", "code_b": "print(1)"}
    result = analyze_token_pair(_request(1, case, "PICAS_STANDARD"))
    card = evidence_card(row, result, reference_summary("none", [], {}, {}))
    assert card["ai_reference_mode"] == "UNAVAILABLE" and not card["relationship_determined"]
    assert any("没有可用" in text for text in card["limitations"])


def test_direct_command_entry_point_without_pytest_import_cache(tmp_path):
    source = make_seed(tmp_path / "source")
    script = Path(__file__).resolve().parents[2] / "experiment/ai_convergence/analyze.py"
    completed = subprocess.run([sys.executable, str(script), "--input", str(source), "--output", str(tmp_path / "cli"), "--no-network"],
                               capture_output=True, text=True, encoding="utf-8", timeout=45)
    assert completed.returncode == 0, completed.stderr
    assert "DEVELOPMENT_ONLY" in completed.stdout


def test_native_parameter_change_is_not_a_fair_frozen_comparison(experiment, tmp_path):
    root, _, _ = experiment
    prepare(root / "run/dataset/dataset.json", tmp_path / "native")
    config = json.loads((root / "run/config.json").read_text(encoding="utf-8"))
    config["jplag"]["minTokens"] = 50
    with pytest.raises(ValueError, match="frozen"):
        validate_baseline(tmp_path / "native", root / "run/dataset/dataset.json", [], config, False)


def test_new_native_scores_cannot_be_imported_with_wrong_dataset_pin(experiment, tmp_path):
    root, _, _ = experiment
    directory = tmp_path / "native"
    prepare(root / "run/dataset/dataset.json", directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    manifest.update(status="FINISHED", dataset_manifest_sha256="0" * 64)
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    config = json.loads((root / "run/config.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="does not align"):
        validate_baseline(directory, root / "run/dataset/dataset.json", [], config, False)


def test_reused_experiment_helpers_are_in_the_source_fingerprint(experiment):
    _, _, manifest = experiment
    assert any(key.replace('\\', '/').endswith('/research_v4_dataset.py') for key in manifest["source_sha256"])
    assert any(key.replace('\\', '/').endswith('/similarity_ablation.py') for key in manifest["source_sha256"])
    assert manifest["dependency_versions"]["pydantic"] and manifest["git_dirty"] is not None
