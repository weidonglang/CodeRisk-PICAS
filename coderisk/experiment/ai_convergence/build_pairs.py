"""Adapter to the existing Research V4 loader; unknown histories stay UNCERTAIN."""
from __future__ import annotations

import argparse
import itertools
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_convergence.protocol import digest, safe_file, write_json, require_private_output
from ai_convergence.validate import validate
from research_v4_dataset import load_research_dataset


def relation_reasons(relation, a, b, sessions, *, file_hashes=None, template_ref=None):
    reasons = []
    if relation is None or relation.claimed_relation == "UNCERTAIN":
        return ["No verified relationship evidence"]
    if a.synthetic or b.synthetic:
        reasons.append("Synthetic fixtures do not qualify as real relationship labels")
    if relation.review_status != "AGREED":
        reasons.append("Two independent human reviews incomplete")
    claimed = relation.claimed_relation
    if "INDEPENDENT" in claimed:
        if a.source_family_id == b.source_family_id or a.parent_sample_id or b.parent_sample_id:
            reasons.append("Independent claim conflicts with shared family or recorded derivation")
        if not relation.independence_evidence_ref:
            reasons.append("Independent relationship evidence absent")
    if claimed.startswith("AI_INDEPENDENT"):
        sa, sb = (sessions.get(s.generation_session_id) for s in (a, b))
        if sa is None or sb is None or sa.generation_session_id == sb.generation_session_id:
            reasons.append("Separate AI session records required")
        else:
            key = lambda s: (s.provider, s.model_id, s.model_version_or_snapshot)
            if (key(sa) == key(sb)) != (claimed == "AI_INDEPENDENT_SAME_MODEL"):
                reasons.append("Declared model relationship contradicts snapshots")
            identify = lambda ref: (file_hashes or {}).get(ref, ref)
            shared = {identify(ref) for ref in sa.shared_upstream_refs} & {identify(ref) for ref in sb.shared_upstream_refs}
            registered_template = identify(template_ref) if template_ref else None
            if shared and (not relation.template_only_shared_upstream_confirmed or shared != {registered_template}):
                reasons.append("Shared upstream is not exclusively the registered reviewed template")
            if any(s.session_independence_basis.startswith("SIMULATED") for s in (sa, sb)):
                reasons.append("Simulation is not independent generation evidence")
    if claimed == "HUMAN_INDEPENDENT" and any(s.origin_type != "HUMAN" or s.ai_assistance_type != "HUMAN_ONLY" for s in (a, b)):
        reasons.append("Human-only relationship contradicts assistance metadata")
    if claimed.startswith("KNOWN_DERIVED") and a.parent_sample_id != b.sample_id and b.parent_sample_id != a.sample_id:
        reasons.append("Direct parent-child evidence absent; no derivation inferred from similarity")
    if claimed == "KNOWN_DERIVED_AI_REWRITE":
        child = a if a.parent_sample_id == b.sample_id else b
        if child.ai_assistance_type not in {"AI_ASSISTED", "PURE_AI"}:
            reasons.append("AI rewrite claim contradicts process metadata")
    if claimed == "KNOWN_DERIVED_HUMAN":
        child = a if a.parent_sample_id == b.sample_id else b
        if child.ai_assistance_type != "HUMAN_ONLY":
            reasons.append("Human rewrite claim contradicts assistance metadata")
    return reasons


def build(source, output, *, max_pairs=10000):
    corpus, texts, validation = validate(source)
    if type(max_pairs) is not int or not 1 <= max_pairs <= 10000:
        raise ValueError("Bounded positive pair cap required")
    samples = {s.sample_id: s for s in corpus.artifacts}
    sessions = {s.generation_session_id: s for s in corpus.sessions}
    relations = {tuple(sorted((r.sample_a, r.sample_b))): r for r in corpus.pair_relations}
    questions = {q.problem_id: q for q in corpus.questions}
    candidates = [pair for pair in itertools.combinations(sorted(samples), 2)
                  if samples[pair[0]].problem_id == samples[pair[1]].problem_id]
    if not candidates or len(candidates) > max_pairs:
        raise ValueError("No pairs or pair cap exceeded; do not silently truncate")
    require_private_output(any(not sample.synthetic for sample in corpus.artifacts), output)
    output.mkdir(parents=True, exist_ok=False)
    cases, index = [], []
    for number, (left, right) in enumerate(candidates):
        a, b = samples[left], samples[right]
        question = questions[a.problem_id]
        relation = relations.get((left, right))
        reasons = relation_reasons(relation, a, b, sessions, file_hashes=validation["file_sha256"], template_ref=question.template_path)
        eligibility_reasons = list(reasons)
        if any(s.functional_check_status != "PASSED" for s in (a, b)):
            eligibility_reasons.append("Primary formal functional gate incomplete/failed; process relation is separate")
        pair_id = "AI-" + digest((corpus.dataset_version + ':' + left + ':' + right).encode())[:20]
        claimed = relation.claimed_relation if relation else "UNCERTAIN"
        label = "UNCERTAIN" if reasons else "INDEPENDENT" if "INDEPENDENT" in claimed else "TRANSFORMED"
        paths = []
        for sample in (a, b):
            extension = ".py" if sample.language == "python" else ".java"
            ref = "samples/" + sample.sample_id + extension
            target = output / ref
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(safe_file(source.parent, sample.code_path), target)
            paths.append(ref)
        synthetic = a.synthetic or b.synthetic
        ai = a.ai_assistance_type in {"PURE_AI", "AI_ASSISTED"} or b.ai_assistance_type in {"PURE_AI", "AI_ASSISTED"}
        applicable_sessions = [sessions[s.generation_session_id] for s in (a, b) if s.generation_session_id]
        provenance = {"source": "Offline recorded generation/creation adapter; not source attribution",
            "license_or_authorization": " | ".join(digest(s.license_or_authorization_ref.encode()) for s in (a, b)),
            "manual_check_status": "VERIFIED" if relation and relation.review_status == "AGREED" else "PENDING",
            "functional_check_status": "PASSED" if all(s.functional_check_status == "PASSED" for s in (a, b)) else "NOT_RUN",
            "template_status": "REGISTERED" if question.template_path else "NONE",
            "parent_source_ref": (a.parent_sample_id or b.parent_sample_id),
            "model_name": " | ".join(s.model_id for s in applicable_sessions) or "NOT_APPLICABLE",
            "prompt_template": " | ".join(s.prompt_sha256 for s in applicable_sessions) or "NOT_APPLICABLE",
            "generation_time": applicable_sessions[0].generation_time_utc if applicable_sessions else "NOT_APPLICABLE"}
        annotation = {} if relation is None else {
            "reviewer_a": relation.reviewer_ids[0] if relation.reviewer_ids else "",
            "reviewer_b": relation.reviewer_ids[1] if len(relation.reviewer_ids) > 1 else "",
            "reviewer_a_type": relation.reviewer_types[0] if relation.reviewer_types else "UNSPECIFIED",
            "reviewer_b_type": relation.reviewer_types[1] if len(relation.reviewer_types) > 1 else "UNSPECIFIED",
            "independence_confirmed": relation.reviewer_independence_confirmed,
            "status": relation.review_status, "label": label, "label_basis": relation.label_evidence_ref or "",
            "reviewed_at": relation.reviewed_at or "", "functional_evidence": " | ".join(s.functional_check_evidence or "" for s in (a, b)),
            "independence_evidence": relation.independence_evidence_ref or "", "shared_template_ref": question.template_id}
        case = {"pair_id": pair_id, "problem_id": question.problem_id, "problem_type": question.problem_family,
            "problem_group": question.problem_family, "dataset_split": question.split,
            "split_preregistered": corpus.provenance.split_preregistered, "source_id": pair_id,
            "source_family_ids": sorted({a.source_family_id, b.source_family_id}),
            "experiment_label": label, "case_type": "AI_REWRITE" if claimed == "KNOWN_DERIVED_AI_REWRITE" else
                "HUMAN_REWRITE" if claimed == "KNOWN_DERIVED_HUMAN" else "INDEPENDENT_SOLUTION",
            "language": question.language, "language_a": question.language, "language_b": question.language,
            "dataset_version": corpus.dataset_version, "data_origin": "SYNTHETIC" if synthetic else "MANUAL",
            "source_type": "synthetic" if synthetic else "ai_assisted" if ai else "manual", "synthetic": synthetic,
            "eligible_for_core_metrics": not eligibility_reasons, "question": {"title": question.title,
                "description": safe_file(source.parent, question.question_path).read_text(encoding="utf-8")},
            "code_a_path": paths[0], "code_b_path": paths[1], "provenance": provenance, "annotation": annotation}
        cases.append(case)
        index.append({"pair_id": pair_id, "sample_a": left, "sample_b": right, "claimed_relation": claimed,
            "resolved_relation": claimed if not reasons else "UNCERTAIN", "reasons": reasons,
            "formal_eligibility_reasons": eligibility_reasons,
            "group_id": validation["groups"][left], "synthetic": synthetic})
    manifest = {"dataset_id": "ai-era-offline", "dataset_version": corpus.dataset_version,
        "status": "DEVELOPMENT_ONLY" if validation["synthetic_count"] else "EXPLORATORY_REQUIRES_FORMAL_GATE",
        "evaluation_registration": {"status": corpus.provenance.status,
            "registered_at": corpus.provenance.registered_at, "reference": corpus.provenance.plan_ref,
            "config_sha256": corpus.provenance.config_sha256},
        "sources": [{"id": "ai-era-adapter", "path": "pairs.json", "format": "RESEARCH_V4_PAIRS_JSON", "include": True}]}
    write_json(output / "dataset.json", manifest)
    write_json(output / "pairs.json", {"dataset_version": corpus.dataset_version, "cases": cases})
    write_json(output / "pair_index.json", index)
    _, _, existing = load_research_dataset(output / "dataset.json")
    write_json(output / "existing_loader_validation.json", existing)
    return manifest, index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-pairs", type=int, default=10000)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    manifest, rows = build(args.input.resolve(), args.output.resolve(), max_pairs=args.max_pairs)
    print({"status": manifest["status"], "pairs": len(rows), "formal_inference": False})


if __name__ == "__main__":
    main()
