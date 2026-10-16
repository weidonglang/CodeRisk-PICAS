"""Thirteen HAND-WRITTEN mock artifacts, not calls or authentic AI/student data."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ai_convergence.protocol import digest, write_json

CASES = {
    "sum": ("validation", "python", "Sum a list with a loop; return the integer total.", [
        "def fold(values):\n    total = 0\n    for item in values:\n        total += item\n    return total\n",
        "def combine(numbers):\n    answer = 0\n    for element in numbers:\n        answer += element\n    return answer\n",
        "def fold(values):\n    total = 0\n    for item in values:\n        total += item\n    return total\n",
        "def fold(values):\n    return sum(values)\n"]),
    "maximum": ("test", "python", "Return the maximum integer in a nonempty list.", [
        "def maximum(values):\n    best = values[0]\n    for item in values:\n        if item > best:\n            best = item\n    return best\n",
        "def maximum(values):\n    return max(values)\n",
        "def maximum(:\n    return 0\n",
        "def maximum(values):\n    return globals()['max'](values)\n"]),
    "count": ("test", "java", "Count integers above zero; return the count.", [
        "class Main { int count(int[] values){int total=0;for(int item:values){if(item>0){total++;}}return total;} }\n",
        "class Main { int tally(int[] items){int answer=0;for(int number:items){if(number>0){answer++;}}return answer;} }\n",
        "class Main { int value=7; int count(){for(int value=0;value<1;value++){}return value;} }\n",
        "class Main { int count(int[] values){return values.length;} }\n"]),
}


def make_seed(output):
    output.mkdir(parents=True, exist_ok=False)
    questions, sessions, samples, relations = [], [], [], []

    def text(ref, value):
        file = output / ref
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value, encoding="utf-8")
        return digest(file.read_bytes())

    text("SYNTHETIC_NOTICE.txt", "Self-authored mock process metadata. No real provider, human review, functional execution or authorization.\n")
    for name, (split, language, question_text, codes) in CASES.items():
        problem = "MOCK-" + name
        qref = "questions/" + name + ".txt"
        prompt_ref = "prompts/" + name + ".txt"
        qhash = text(qref, question_text)
        phash = text(prompt_ref, "MOCK ONLY. " + question_text)
        template_ref = "templates/sum.py" if name == "sum" else None
        if template_ref:
            text(template_ref, codes[0])
        questions.append({"problem_id": problem, "problem_family": "MOCK-FAMILY-" + name,
            "language": language, "title": "Synthetic " + name, "question_path": qref,
            "question_text_sha256": qhash, "difficulty_proxy": "LOW", "solution_space_proxy": "UNKNOWN",
            "template_id": "MOCK-TEMPLATE-SUM" if template_ref else None, "template_path": template_ref,
            "hidden_test_policy": "NOT_RUN: no supplied code is executed", "course_ai_policy": "UNKNOWN",
            "confidentiality": "SYNTHETIC", "license_or_authorization_ref": "SYNTHETIC_NOTICE.txt", "split": split})
        for i, code in enumerate(codes):
            sample = problem + "-" + str(i)
            session = sample + "-SESSION"
            model = "MOCK-MODEL-A" if i < 2 else "MOCK-MODEL-B"
            ref = "code/" + sample + (".py" if language == "python" else ".java")
            chash = text(ref, code)
            raw_ref = "raw/" + sample + ".txt"
            raw_hash = text(raw_ref, code)
            session_ref = "sessions/" + session + ".json"
            write_json(output / session_ref, {"generation_session_id": session, "problem_id": problem,
                "model_id": model, "prompt_sha256": phash, "raw_output_sha256": raw_hash,
                "synthetic": True, "note": "Hand-written fixture, not a model response"})
            sessions.append({"generation_session_id": session, "problem_id": problem,
                "source_family_id": sample + "-FAMILY", "session_independence_basis": "SIMULATED_FOR_PIPELINE_ONLY",
                "provider": "MOCK-A" if i < 2 else "MOCK-B", "model_id": model,
                "model_version_or_snapshot": "MOCK-SNAPSHOT-NOT-A-REAL-MODEL", "access_mode": "SYNTHETIC_FIXTURE",
                "generation_time_utc": "2026-10-12T00:00:00Z", "prompt_id": "MOCK-PROMPT-" + name,
                "prompt_family": "MOCK-PROMPT-FAMILY", "prompt_sha256": phash,
                "full_prompt_storage_ref": prompt_ref, "session_record_ref": session_ref,
                "temperature": None, "top_p": None, "seed_if_supported": None,
                "settings_semantics": "No generation occurred; settings unknown/not applicable",
                "revision_count": 0, "human_edits": False, "shared_upstream_refs": [], "synthetic": True})
            samples.append({"sample_id": sample, "problem_id": problem, "source_family_id": sample + "-FAMILY",
                "generation_session_id": session, "origin_type": "AI", "ai_assistance_type": "PURE_AI",
                "parent_sample_id": None, "code_path": ref, "language": language, "code_sha256": chash,
                "syntax_status": "NOT_RUN", "functional_check_status": "NOT_RUN", "functional_check_evidence": None,
                "raw_output_ref": raw_ref, "license_or_authorization_ref": "SYNTHETIC_NOTICE.txt",
                "redistribution_allowed": True, "privacy_status": "SYNTHETIC", "synthetic": True, "split": split})
        relations.append({"sample_a": problem + "-0", "sample_b": problem + "-2",
            "claimed_relation": "AI_INDEPENDENT_CROSS_MODEL", "review_status": "NOT_REVIEWED",
            "reviewer_ids": [], "reviewer_types": [], "reviewer_independence_confirmed": False,
            "reviewed_code_sha256": [], "label_evidence_ref": None, "independence_evidence_ref": None,
            "reviewed_at": None, "template_only_shared_upstream_confirmed": False})
    parent = samples[0]
    child_id = "MOCK-sum-controlled-rename"
    child_path = "code/" + child_id + ".py"
    child_hash = text(child_path, CASES["sum"][3][1])
    samples.append({**parent, "sample_id": child_id, "generation_session_id": None, "origin_type": "HUMAN",
        "ai_assistance_type": "HUMAN_ONLY", "parent_sample_id": parent["sample_id"],
        "code_path": child_path, "code_sha256": child_hash, "raw_output_ref": child_path})
    relations.append({**relations[0], "sample_a": parent["sample_id"], "sample_b": child_id,
                      "claimed_relation": "KNOWN_DERIVED_HUMAN"})
    data = {"protocol_version": "ai-convergence-1.0", "dataset_version": "ai-era-mock-seed-1",
        "provenance": {"status": "UNREGISTERED", "registered_at": None, "plan_ref": None,
            "config_sha256": None, "split_preregistered": False, "user_study_consent_ref": None},
        "questions": questions, "sessions": sessions, "artifacts": samples, "pair_relations": relations}
    write_json(output / "corpus.json", data)
    return output / "corpus.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(make_seed(args.output.resolve()))
