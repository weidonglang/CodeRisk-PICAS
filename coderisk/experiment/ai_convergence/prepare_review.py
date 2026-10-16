"""Reuse the existing blinded HUMAN workbench; never fill labels or participant outcomes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_convergence.protocol import digest, write_json, require_private_output
from ai_convergence.validate import validate
from research_v4_dataset import load_research_dataset
from prepare_annotation_workbench import render_workbench
from run_fair_evaluation import write_csv


def prepare(source, dataset, output):
    corpus, _, _ = validate(source)
    require_private_output(any(not sample.synthetic for sample in corpus.artifacts), output)
    _, cases, _ = load_research_dataset(dataset)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for case in cases:
        rows.append({"review_id": "R-" + digest(case["pair_id"].encode())[:20], "dataset": corpus.dataset_version,
            "problem_id": case["problem_id"], "language": case["language"], "experiment_label": "UNCERTAIN",
            "annotation_status": "AWAITING_TWO_INDEPENDENT_REVIEWS", "eligible_for_core_metrics": False,
            "source_a": {"code_path": str(dataset.parent / case["code_a_path"]), "code_sha256_bytes": digest((dataset.parent / case["code_a_path"]).read_bytes()), "functional_evidence": "NOT_AUTHENTICATED"},
            "source_b": {"code_path": str(dataset.parent / case["code_b_path"]), "code_sha256_bytes": digest((dataset.parent / case["code_b_path"]).read_bytes()), "functional_evidence": "NOT_AUTHENTICATED"}})
    queue = output / "blind_batch.jsonl"
    with queue.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    (output / "workbench.html").write_text(render_workbench(rows, digest(queue.read_bytes())), encoding="utf-8")
    write_csv(output / "usability_record_template.csv", [{"participant_id": "", "consent_ref": "", "question_id": "",
        "counterbalanced_order": "", "report_variant": "", "task": task, "answer": "", "gold_answer_ref": "",
        "elapsed_seconds": "", "certainty_before": "", "certainty_after": "", "observer_note": ""}
        for task in ("IDENTIFY_SHARED_TEMPLATE", "LOCATE_MATCHED_FRAGMENT", "IDENTIFY_MISSING_PROVENANCE", "AVOID_OVERCONFIDENT_SOURCE_CLAIM")])
    report = {"status": "FORMAL_BLOCKED_NO_REAL_REVIEW_OR_USER_STUDY", "pair_count": len(rows),
        "human_reviews": 0, "study_participants": 0, "synthetic": any(s.synthetic for s in corpus.artifacts),
        "workbench": "REUSED_EXISTING_OFFLINE_HUMAN_REVIEW_TOOL", "consent_verified": False,
        "label_basis": "Leave unknown; reviewer scores cannot establish missing source histories"}
    write_json(output / "FORMAL_BLOCKED.json", report)
    (output / "FORMAL_BLOCKED.md").write_text("# FORMAL_BLOCKED\n\n需要真实授权、生成过程、功能验证、两位真人复核及预注册。\n\n没有真实参与者，不得声称效率提升。\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.input.resolve(), args.dataset.resolve(), args.output.resolve())["status"])
