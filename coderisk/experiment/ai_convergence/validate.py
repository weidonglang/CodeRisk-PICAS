"""No-network process checks and connected split isolation. Does not certify truth."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_convergence.protocol import read_corpus, safe_file, unique, digest, write_json
from research_protocol import connected_groups


def validate(file):
    corpus = read_corpus(file)
    root = file.parent
    questions = unique(corpus.questions, "problem_id")
    sessions = unique(corpus.sessions, "generation_session_id")
    samples = unique(corpus.artifacts, "sample_id")
    files, texts = {}, {}

    def record(ref):
        target = safe_file(root, ref)
        files[ref] = digest(target.read_bytes())
        return target

    for question in questions.values():
        if digest(record(question.question_path).read_bytes()) != question.question_text_sha256:
            raise ValueError("Question content hash mismatch")
        record(question.license_or_authorization_ref)
        if (question.template_id is None) != (question.template_path is None):
            raise ValueError("Template ID and path must be registered together")
        if question.template_path:
            record(question.template_path)
    record_hashes, captured_sessions = set(), {}
    for session in sessions.values():
        if session.problem_id not in questions:
            raise ValueError("Session question missing")
        if digest(record(session.full_prompt_storage_ref).read_bytes()) != session.prompt_sha256:
            raise ValueError("Prompt hash mismatch")
        session_file = record(session.session_record_ref)
        if files[session.session_record_ref] in record_hashes:
            raise ValueError("Duplicated generation session record; separate IDs are not evidence")
        record_hashes.add(files[session.session_record_ref])
        import json
        captured = json.loads(session_file.read_text(encoding="utf-8"))
        if not isinstance(captured, dict):
            raise ValueError("Session capture must be an object")
        captured_sessions[session.generation_session_id] = captured
        for key in ("generation_session_id", "problem_id", "model_id", "prompt_sha256"):
            if captured.get(key) != getattr(session, key):
                raise ValueError("Session capture contradicts declared metadata")
        if session.synthetic != (session.access_mode == "SYNTHETIC_FIXTURE"):
            raise ValueError("Synthetic access mode mismatch")
        if not session.synthetic and (session.provider.startswith("MOCK") or session.model_id.startswith("MOCK")):
            raise ValueError("Mock session cannot be promoted to real data")
        for ref in session.shared_upstream_refs:
            record(ref)
        if session.attempt_status in {"FAILED", "TRUNCATED"} and not session.error_or_truncation_ref:
            raise ValueError("Failed/truncated generation needs a recorded failure reference")
        if session.error_or_truncation_ref:
            record(session.error_or_truncation_ref)
    grouping = []
    for sample in samples.values():
        question = questions.get(sample.problem_id)
        if question is None or sample.language != question.language or sample.split != question.split:
            raise ValueError("Sample question/language/split mismatch")
        code = record(sample.code_path).read_bytes()
        if digest(code) != sample.code_sha256:
            raise ValueError("Code byte hash mismatch")
        texts[sample.sample_id] = code.decode("utf-8")
        raw_output = record(sample.raw_output_ref)
        record(sample.license_or_authorization_ref)
        if sample.functional_check_status != "NOT_RUN" and not sample.functional_check_evidence:
            raise ValueError("Declared function check requires a recorded evidence file")
        if sample.functional_check_evidence:
            record(sample.functional_check_evidence)
        if sample.synthetic != (sample.privacy_status == "SYNTHETIC"):
            raise ValueError("Synthetic provenance/visibility mismatch")
        if not sample.synthetic and question.confidentiality == "SYNTHETIC":
            raise ValueError("Synthetic problem cannot qualify as real benchmark")
        if sample.origin_type == "AI" or sample.ai_assistance_type in {"PURE_AI", "AI_ASSISTED"}:
            session = sessions.get(sample.generation_session_id)
            if session is None or session.problem_id != sample.problem_id or session.synthetic != sample.synthetic:
                raise ValueError("AI artifact needs matching generation session")
            if session.source_family_id != sample.source_family_id:
                raise ValueError("Session source-family mismatch")
            if captured_sessions[session.generation_session_id].get("raw_output_sha256") != digest(raw_output.read_bytes()):
                raise ValueError("Raw output hash does not match captured session")
        elif sample.generation_session_id is not None:
            raise ValueError("Human/unknown sample cannot masquerade as AI generation")
        if sample.parent_sample_id is not None:
            parent = samples.get(sample.parent_sample_id)
            if parent is None or parent.sample_id == sample.sample_id or parent.problem_id != sample.problem_id:
                raise ValueError("Invalid or absent parent sample")
        families = ["SOURCE:" + sample.source_family_id, "PROBLEM_FAMILY:" + question.problem_family,
                    "QUESTION_TEXT:" + question.question_text_sha256]
        if sample.generation_session_id:
            families.append("SESSION:" + sample.generation_session_id)
        if sample.parent_sample_id:
            families.append("ANCESTRY:" + sample.parent_sample_id)
        families.append("ANCESTRY:" + sample.sample_id)
        # Reuse the existing grouping algorithm; include byte AND normalized text hashes.
        grouping.append({"pair_id": sample.sample_id, "problem_id": sample.problem_id, "source_id": sample.sample_id,
                         "source_family_ids": families, "code_a_sha256": sample.code_sha256,
                         "code_b_sha256": digest(texts[sample.sample_id].encode())})
    for sample in samples.values():
        seen, current = set(), sample
        while current.parent_sample_id is not None:
            if current.sample_id in seen:
                raise ValueError("Parent ancestry cycle rejected")
            seen.add(current.sample_id)
            current = samples[current.parent_sample_id]
    groups = connected_groups(grouping)
    split_groups = defaultdict(set)
    for sample in samples.values():
        split_groups[groups[sample.sample_id]].add(sample.split)
    if any(len(splits) > 1 for splits in split_groups.values()):
        raise ValueError("Connected problem/family/session/parent/hash leakage across validation/test")
    keys = set()
    for relation in corpus.pair_relations:
        key = tuple(sorted((relation.sample_a, relation.sample_b)))
        if key in keys or relation.sample_a == relation.sample_b or not set(key) <= samples.keys():
            raise ValueError("Duplicate, self or absent pair relation")
        keys.add(key)
        a, b = (samples[name] for name in key)
        if a.problem_id != b.problem_id:
            raise ValueError("Relationship must compare one question")
        for ref in (relation.label_evidence_ref, relation.independence_evidence_ref):
            if ref:
                record(ref)
        if relation.review_status == "AGREED" and (len(relation.reviewer_ids) != 2 or len(set(relation.reviewer_ids)) != 2
            or relation.reviewer_types != ["HUMAN", "HUMAN"] or not relation.reviewer_independence_confirmed
            or sorted(relation.reviewed_code_sha256) != sorted((a.code_sha256, b.code_sha256))
            or not relation.label_evidence_ref or not relation.reviewed_at):
            raise ValueError("Agreed label needs two independent declared HUMAN reviews tied to source hashes")
    for ref in (corpus.provenance.plan_ref, corpus.provenance.user_study_consent_ref):
        if ref:
            record(ref)
    sensitivity = {}
    for field in ("prompt_family", "model_version_or_snapshot"):
        splits = defaultdict(set)
        for sample in samples.values():
            if sample.generation_session_id:
                session = sessions[sample.generation_session_id]
                splits[getattr(session, field)].add(sample.split)
        sensitivity[field] = {"cross_split_values": sum(len(s) > 1 for s in splits.values()),
                              "status": "SENSITIVITY_ONLY_NOT_MODEL_DISJOINT_CLAIM"}
    report = {"status": "DEVELOPMENT_ONLY" if any(s.synthetic for s in samples.values()) else "ELIGIBLE_DESCRIPTIVE_NOT_FORMAL",
              "sample_count": len(samples), "session_count": len(sessions), "problem_count": len(questions),
              "connected_group_count": len(split_groups), "synthetic_count": sum(s.synthetic for s in samples.values()),
              "split_counts": dict(Counter(s.split for s in samples.values())), "file_sha256": files,
              "attempt_status_counts": dict(Counter(s.attempt_status for s in sessions.values())),
              "sessions_without_artifact": len(set(sessions) - {s.generation_session_id for s in samples.values() if s.generation_session_id}),
              "groups": groups, "sensitivity": sensitivity, "network_calls": 0, "code_executions": 0,
              "disclaimer": "Checks declared records, not genuine consent, independent authorship or human identity"}
    return corpus, texts, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-network", action="store_true", help="Always enforced, not an optional safety mode")
    args = parser.parse_args()
    _, _, report = validate(args.input.resolve())
    write_json(args.output.resolve(), report)
    print({key: report[key] for key in ("status", "sample_count", "session_count", "network_calls")})


if __name__ == "__main__":
    main()
