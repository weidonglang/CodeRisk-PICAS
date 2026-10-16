"""Offline value experiment using the UNCHANGED existing production and evaluation modules."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_convergence.build_pairs import build
from ai_convergence.context import evidence_card, preflight_report, reference_summary
from ai_convergence.protocol import digest, safe_file, write_json
from ai_convergence.descriptive_stats import distribution, paired_cluster_interval
from ai_convergence.validate import validate
from similarity_ablation import extract_case, evaluate, validate_config, quality_blockers, method_score, binary_metrics
from check_formal_readiness import case_readiness
from research_v4_dataset import load_research_dataset
from run_fair_evaluation import write_csv
from run_research_v4 import _request
from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.token_similarity import analyze_token_pair, _fingerprints, tokenize_code_with_locations

DEFAULT_CONFIG = Path(__file__).with_name("config.example.json")


def formal_gate(corpus, cases, dataset, config_hash):
    blockers = quality_blockers(cases, dataset, config_hash)
    for case in cases:
        if case["eligible_for_core_metrics"]:
            blockers.extend(case["pair_id"] + ': ' + reason for reason in case_readiness(case))
    for split in ("validation", "test"):
        pool = [case for case in cases if case["split"] == split and case["eligible_for_core_metrics"]]
        if not any(c["experiment_label"] == "INDEPENDENT" for c in pool) or not any(c["experiment_label"] == "TRANSFORMED" for c in pool):
            blockers.append(split + ': trusted independent and known-derived labels both required')
    return sorted(set(blockers))


def unestimable_metrics(evaluation):
    for metric in evaluation["metrics"]:
        for field in ("tp", "fp", "tn", "fn", "precision", "recall", "f1", "fpr", "natural_similar_fpr", "suspicious_recall",
                      "pr_auc_ap_score", "pr_auc_ap_margin"):
            if field in metric:
                metric[field] = None
        metric["status"] = "NOT_ESTIMABLE_UNTRUSTED_RELATIONSHIP_LABELS"


def metrics_by_relation(rows, evaluation, config, formal):
    output = []
    relations = ("HUMAN_INDEPENDENT", "AI_INDEPENDENT_SAME_MODEL", "AI_INDEPENDENT_CROSS_MODEL",
                 "KNOWN_DERIVED_HUMAN", "KNOWN_DERIVED_AI_REWRITE")
    for method in config["methods"]:
        predictions = {p["pair_id"]: p for p in evaluation["predictions"] if p["method"] == method["name"] and p["in_common_support"]}
        for relation in relations:
            pool = [row for row in rows if row["split"] == "test" and row["resolved_relation"] == relation and row["pair_id"] in predictions]
            item = {"method": method["name"], "relation": relation, "scope": "COMMON_TEST_ONLY",
                    "n_trusted": len(pool), **binary_metrics(pool, [predictions[r["pair_id"]]["predicted"] for r in pool])}
            item["status"] = "FORMAL_RELATIONSHIP_SUBGROUP" if formal and pool else "NOT_ESTIMABLE_NO_TRUSTED_DENOMINATOR"
            if not formal or not pool:
                unestimable_metrics({"metrics": [item]})
            item["FPR_independent_AI"] = item["fpr"] if relation.startswith("AI_INDEPENDENT") else None
            item["meaning"] = "Risk-candidate frequency among reviewed independent AI pairs, not AI-use error rate or misconduct rate"
            output.append(item)
    return output


def run(source, output, config_path=DEFAULT_CONFIG, *, formal=False, jplag_dir=None):
    corpus, texts, intake = validate(source)
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    validate_config(config)
    if config.get("convergenceProtocolVersion") != "ai-convergence-1.0":
        raise ValueError("Frozen AI convergence protocol required")
    paired_cluster_interval([], seed=config["randomSeed"], replicates=config["bootstrapReplicates"], minimum_clusters=config["minimumClusters"])
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    build(source, output / "dataset")
    dataset, cases, loader_validation = load_research_dataset(output / "dataset/dataset.json")
    index = {row["pair_id"]: row for row in json.loads((output / "dataset/pair_index.json").read_text(encoding="utf-8"))}
    blockers = formal_gate(corpus, cases, dataset, digest(config_bytes))
    if formal and blockers:
        write_json(output / "FORMAL_BLOCKED.json", {"status": "FORMAL_BLOCKED", "blockers": blockers})
        (output / "FORMAL_BLOCKED.md").write_text('# FORMAL_BLOCKED\n\n' + '\n'.join('- ' + b for b in blockers), encoding="utf-8")
        return {"status": "FORMAL_BLOCKED", "exit_code": 2, "formal_eligible_pairs": 0, "network_calls": 0}
    samples = {s.sample_id: s for s in corpus.artifacts}
    sessions = {s.generation_session_id: s for s in corpus.sessions}
    questions = {q.problem_id: q for q in corpus.questions}
    canonical = {s.sample_id: canonicalize_code(texts[s.sample_id], s.language,
                 tokenize_code_with_locations(texts[s.sample_id], s.language)) for s in corpus.artifacts}
    references = {q: reference_summary(q, corpus.artifacts, canonical, sessions) for q in questions}
    for question_id, reference in references.items():
        declared_independent = {pair["sample_" + side] for pair in index.values() for side in ("a", "b")
            if pair["resolved_relation"].startswith("AI_INDEPENDENT") and not pair["synthetic"]
            and samples[pair["sample_" + side]].problem_id == question_id
            and samples[pair["sample_" + side]].functional_check_status == "PASSED"}
        reference["independent_reference_pool_size"] = len(declared_independent)
        reference["independence_authenticity_verified_by_tool"] = False
    rows, cards = [], []
    for number, case in enumerate(cases):
        pair_start = time.perf_counter()
        pair = index[case["pair_id"]]
        row = extract_case(case, number + 1, pair["group_id"])
        row["formal_eligible"] = bool(formal and not blockers and case["eligible_for_core_metrics"])
        if not formal or not case["eligible_for_core_metrics"]:
            row["label"] = "UNCERTAIN"
        a, b = (samples[pair["sample_" + side]] for side in ("a", "b"))
        sa, sb = (sessions.get(s.generation_session_id) for s in (a, b))
        ca, cb = canonical[a.sample_id], canonical[b.sample_id]
        available = ca.mode in {"scope-aware-python", "scope-aware-java"} and cb.mode == ca.mode
        row["warnings"] = ' | '.join(dict.fromkeys([item for item in (row["warnings"], ca.reason, cb.reason) if item]))
        row.update({"sample_a": a.sample_id, "sample_b": b.sample_id, "claimed_relation": pair["claimed_relation"],
            "resolved_relation": pair["resolved_relation"], "relationship_reasons": ' | '.join(pair["reasons"]),
            "formal_eligibility_reasons": ' | '.join(pair["formal_eligibility_reasons"]),
            "model_combo": ' | '.join(sorted(s.provider + '/' + s.model_id + '/' + s.model_version_or_snapshot for s in (sa, sb) if s)),
            "prompt_combo": ' | '.join(sorted(s.prompt_family for s in (sa, sb) if s)),
            "canonical_minus_raw": row["canonical"] - row["raw"] if row["canonical"] is not None else None,
            "complete_c_equal": ca.tokens == cb.tokens if available else None,
            "ngram_set_equal": _fingerprints(ca.tokens) == _fingerprints(cb.tokens) if available else None,
            "gold_orbit_relation": "UNKNOWN_NOT_INFERRED_FROM_SCORES",
            "functional_stratum": ' | '.join(sorted(s.functional_check_status for s in (a, b))),
            "syntax_stratum": ' | '.join(sorted(s.syntax_status for s in (a, b)))})
        request = _request(number + 1, case, "PICAS_STANDARD")
        question = questions[row["problem_id"]]
        if question.template_path:
            request = request.model_copy(update={"question": request.question.model_copy(update={
                "starter_code": safe_file(source.parent, question.template_path).read_text(encoding="utf-8"),
                "starter_language": question.language, "starter_source": "REGISTERED_LOCAL_TEMPLATE"})})
        result = analyze_token_pair(request)
        if abs(result.weighted_similarity_score - row["full"]) > 1e-6 or result.dynamic_threshold != row["dynamic_threshold"]:
            raise AssertionError("Read-only context must not alter production score or threshold")
        card = evidence_card(row, result, references[row["problem_id"]])
        row["effective_length_min"] = min(v for v in card["effective_code_length"].values() if v is not None)
        row["length_stratum"] = "SHORT_LE_40" if row["effective_length_min"] <= 40 else "LONGER_THAN_40"
        row["template_stratum"] = "DOMINANT_GE_50PCT" if max(card["template_coverage"].get("submission" + side, {}).get("templateCoverage", 0) for side in ("A", "B")) >= .5 else "OTHER"
        row["offline_pair_total_ms"] = round((time.perf_counter() - pair_start) * 1000, 6)
        rows.append(row)
        cards.append(card)
    evaluation = evaluate(rows, config)
    if not formal:
        unestimable_metrics(evaluation)
    relation_metrics = metrics_by_relation(rows, evaluation, config, formal)
    # Optional existing JPlag outputs must be pinned to this adapter dataset and source hashes.
    baseline = {"status": "NOT_RUN", "reason": "No current dataset-aligned JPlag run supplied"}
    if jplag_dir:
        from ai_convergence.jplag import validate_baseline
        baseline = validate_baseline(jplag_dir, output / "dataset/dataset.json", rows, config, formal)
        write_csv(output / "baseline_comparison_metrics.csv", baseline["methods"])
    distributions = []
    for dimension in ("problem_id", "model_combo", "prompt_combo", "length_stratum", "template_stratum", "functional_stratum", "syntax_stratum"):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row[dimension]].append(row)
        for value, group in sorted(grouped.items()):
            for method in config["methods"]:
                distributions.append({"dimension": dimension, "group": value, "method": method["name"],
                    "scope": "FORMAL_ELIGIBLE" if formal else "DEVELOPMENT_ONLY" if intake["synthetic_count"] else "EXPLORATORY",
                    **distribution([method_score(row, method) for row in group], len(group))})
            distributions.append({"dimension": dimension, "group": value, "method": "CANONICAL_MINUS_RAW",
                "scope": "DESCRIPTIVE_NOT_ACCURACY", **distribution([r["canonical_minus_raw"] for r in group], len(group))})
    cluster = paired_cluster_interval([r for r in rows if r["split"] == "test"], seed=config["randomSeed"],
        replicates=config["bootstrapReplicates"], minimum_clusters=config["minimumClusters"])
    cluster["scope"] = "TEST_COMPONENTS_ONLY_NO_VALIDATION_POOLING"
    for name, data in {"validation": intake, "existing_loader": loader_validation, "config": config,
                       "results": {"rows": rows, "evaluation": evaluation, "baseline": baseline, "cluster": cluster},
                       "context_evidence": cards}.items():
        write_json(output / (name + ".json"), data)
    write_csv(output / "scores.csv", rows)
    write_csv(output / "metrics.csv", evaluation["metrics"])
    write_csv(output / "relation_metrics.csv", relation_metrics)
    write_csv(output / "distributions.csv", distributions)
    write_csv(output / "failures.csv", [r for r in rows if r["warnings"] or r["functional_stratum"] != "PASSED | PASSED" or r["relationship_reasons"]])
    write_csv(output / "borderline.csv", [p for p in evaluation["predictions"] if p["score"] is not None and p["threshold"] is not None and abs(p["score"] - p["threshold"]) <= config["borderlineMargin"]])
    write_json(output / "assignment_preflight.json", [preflight_report(questions[q], references[q], [c for c in cards if c["question_id"] == q]) for q in questions])
    git = subprocess.run(["git", "--no-optional-locks", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[3], capture_output=True, text=True, encoding="utf-8", errors="replace")
    dirty = subprocess.run(["git", "--no-optional-locks", "status", "--porcelain"], cwd=Path(__file__).resolve().parents[3], capture_output=True, text=True, encoding="utf-8", errors="replace")
    app = Path(__file__).resolve().parents[2] / "analysis-service-python/app"
    source_files = sorted(Path(__file__).parent.rglob("*.py")) + sorted(app.rglob("*.py"))
    source_files += [Path(__file__).parent.parent / file for file in ("similarity_ablation.py", "run_fair_evaluation.py",
        "research_v4_dataset.py", "research_protocol.py", "check_formal_readiness.py", "run_research_v4.py",
        "research_v4_jplag.py", "prepare_annotation_workbench.py", "annotation_workbench.html")]
    dependencies = {}
    for package in ("pydantic", "tree-sitter", "matplotlib"):
        try:
            dependencies[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            dependencies[package] = None
    manifest = {"status": "FORMAL_ELIGIBLE_DECLARED_RECORDS" if formal else "DEVELOPMENT_ONLY" if intake["synthetic_count"] else "EXPLORATORY_FORMAL_BLOCKED",
        "dataset_version": corpus.dataset_version, "config_sha256": digest(config_bytes), "input_sha256": digest(source.read_bytes()),
        "input_file_sha256": intake["file_sha256"], "source_sha256": {str(p.relative_to(Path(__file__).resolve().parents[3])): digest(p.read_bytes()) for p in source_files},
        "git_commit": git.stdout.strip() if git.returncode == 0 else None, "python": platform.python_version(),
        "git_dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None, "dependency_versions": dependencies,
        "formula_version": "FORMULA_SPEC_V1", "algorithm_version": "UNCHANGED_PRODUCTION_PICAS_STANDARD",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "duration_seconds": round(time.perf_counter() - started, 6),
        "random_seed": config["randomSeed"], "pair_count": len(rows), "connected_groups": intake["connected_group_count"],
        "formal_eligible_pairs": sum(row["formal_eligible"] for row in rows), "formal_blockers": blockers,
        "live_model_calls": 0, "network_calls": 0, "code_executions": 0, "production_formula_changed": False,
        "jplag_status": baseline["status"], "decision": "INSUFFICIENT_EVIDENCE"}
    write_json(output / "run_manifest.json", manifest)
    from ai_convergence.report import render_reports
    render_reports(output, manifest, rows, distributions, cards)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--jplag-dir", type=Path)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    result = run(args.input.resolve(), args.output.resolve(), args.config.resolve(), formal=args.formal,
                 jplag_dir=args.jplag_dir.resolve() if args.jplag_dir else None)
    print({key: result[key] for key in ("status", "formal_eligible_pairs", "network_calls")})
    raise SystemExit(result.get("exit_code", 0))


if __name__ == "__main__":
    main()
