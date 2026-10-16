"""Aggregate, source-free reports and optional offline plots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_convergence.protocol import write_json


def render_reports(output, manifest, rows, distributions, cards):
    lines = ["# AI-era value experiment", "", '**' + manifest["status"] + '**', "",
        "This runner never calls models; imported records are not authenticated by the tool.",
        "Mock sessions, if present, are hand-written fixtures, not independent AI outputs.",
        "Source history cannot be reconstructed from identical problem/code observations.", "",
        f"Pairs: {len(rows)}; connected groups: {manifest['connected_groups']}; formal eligible: {manifest['formal_eligible_pairs']}.",
        "",
        "| Question | Method | Available / requested pairs | Mean | Median | P90 | P95 |",
        "| --- | --- | --- | --- | --- | --- | --- |"]
    for item in distributions:
        if item["dimension"] != "problem_id":
            continue
        def display(value):
            return "N/A" if value is None else f"{value:.4f}"
        lines.append('| ' + ' | '.join([item["group"], item["method"], f"{item['n_available']}/{item['n_requested']}",
            *[display(item[field]) for field in ("mean", "median", "p90", "p95")]]) + ' |')
    lines += ["", "Scores above are descriptive, not FPR/F1 or proof of source relationship.",
        "PICAS fixed and rule modes share the same score; only their operating thresholds differ.",
        "Unknown relationship denominators remain N/A. Pair counts are not independent observations.",
        "No orbit membership is inferred from canonical or n-gram equality.",
        "JPlag uses current source hashes; see the baseline cohort, coverage and missing rows separately.",
        "", "## Decision", "", "INSUFFICIENT_EVIDENCE: no formal advantage or teacher-efficiency claim.", ""]
    (output / "REPORT.md").write_text('\n'.join(lines), encoding="utf-8")
    cards_text = ["# Submission review context", "", "Read-only prototype; not a behavioral verdict.", ""]
    for card in cards:
        cards_text += ['## ' + card["comparison_id"], '',
            f"Question: {card['question_id']}; score {card['picas_score']}; threshold {card['threshold']}; risk {card['risk_level']}.",
            f"AI reference mode: {card['ai_reference_mode']}; verified independent pool: {card['independent_reference_pool_size']}.",
            f"Parse warning: {card['parse_warnings'] or 'none'}.", '',
            *('- ' + item for item in card["limitations"]), '', *('- ' + item for item in card["review_questions"]), '']
    (output / "submission_review.md").write_text('\n'.join(cards_text), encoding="utf-8")
    preflight = json.loads((output / "assignment_preflight.json").read_text(encoding="utf-8"))
    text = ["# 出题前预检（离线原型）", "", "不预测真实学生抄袭率，不向第三方发送题目。", ""]
    for item in preflight:
        text += ['## ' + item["question_id"], '', item["reference"]["message"], item["warning"],
                 *('- ' + choice for choice in item["teaching_options"]), '']
    (output / "assignment_preflight.md").write_text('\n'.join(text), encoding="utf-8")
    plot_status = plot(output, rows)
    write_json(output / "plot_status.json", plot_status)


def plot(output, rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return {"status": "NOT_RUN", "reason": "Existing experiment matplotlib dependency unavailable; CSV intact"}
    questions = sorted({r["problem_id"] for r in rows})
    panels = min(3, len(questions))
    if not panels:
        return {"status": "NOT_RUN", "reason": "No pairs"}
    from similarity_ablation import method_score
    config = json.loads((output / "config.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(len(questions) // panels + bool(len(questions) % panels), panels,
                             figsize=(5 * panels, 4 * (len(questions) // panels + bool(len(questions) % panels))), squeeze=False)
    for axis, question in zip(axes.flat, questions):
        group = [r for r in rows if r["problem_id"] == question]
        data = [[value for row in group if (value := method_score(row, method)) is not None] for method in config["methods"]]
        labels = [m["name"].replace("PICAS_", "P-").replace("CANONICAL", "CAN").replace("_FIXED", "").replace("_ONLY", "") for m in config["methods"]]
        import inspect
        label_argument = "tick_labels" if "tick_labels" in inspect.signature(axis.boxplot).parameters else "labels"
        axis.boxplot(data, **{label_argument: labels})
        axis.set_title(question + f" (requested pairs={len(group)})", fontsize=10)
        axis.set_ylim(-.05, 1.05)
        axis.tick_params(axis="x", labelrotation=60, labelsize=7)
        axis.set_ylabel("Descriptive similarity, not accuracy")
    for axis in list(axes.flat)[len(questions):]:
        axis.axis("off")
    mode = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))["status"]
    fig.suptitle(mode + " - connected pairs are dependent", fontsize=11)
    fig.tight_layout()
    fig.savefig(output / "question_distributions.png", dpi=140)
    plt.close(fig)
    return {"status": "COMPLETED", "plot": "question_distributions.png", "statistical_inference": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    directory = args.run_dir.resolve()
    result = json.loads((directory / "results.json").read_text(encoding="utf-8"))
    manifest = json.loads((directory / "run_manifest.json").read_text(encoding="utf-8"))
    print({"status": manifest["status"], "report": str(directory / "REPORT.md"), "regeneration": "NOT_PERFORMED_IMMUTABLE_RUN"})
