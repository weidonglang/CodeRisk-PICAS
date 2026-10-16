"""Read-only context cards; final code never identifies the authoring history."""
from __future__ import annotations

import hashlib
import json


COMMON_LIMITATIONS = [
    "相同题目与最终源码不能区分独立生成和复制这两种历史。",
    "相似分数、规范化和参考匹配不能证明来源关系、AI使用、语义等价或课程合规性。",
    "参考集合有选择偏差；分数更高不代表方法更好。",
    "本卡只增加复核上下文，不修改生产分数、阈值、风险等级或处置。",
]
QUESTIONS = ["题目是否限制了实现方式，或存在共同模板？", "非模板片段还有多少，原文位置能否核对？",
             "解析或规范化是否降级？", "是否有经同意保存的提示、版本、修订或独立创作证据？",
             "课程AI政策是什么，是否由有权限的教师人工解释？"]


def reference_summary(question_id, artifacts, canonical, sessions):
    selected = [s for s in artifacts if s.problem_id == question_id and s.generation_session_id]
    if not selected:
        return {"mode": "UNAVAILABLE", "sample_count": 0, "model_count": 0, "session_count": 0,
                "independent_reference_pool_size": 0, "canonical_available": 0, "unique_forms": None,
                "message": "没有可用的AI参考证据。"}
    synthetic = any(s.synthetic for s in selected)
    forms = [hashlib.sha256(json.dumps(canonical[s.sample_id].tokens).encode()).hexdigest() for s in selected
             if canonical[s.sample_id].mode in {"scope-aware-python", "scope-aware-java"}]
    model_keys = {(sessions[s.generation_session_id].provider, sessions[s.generation_session_id].model_id,
                   sessions[s.generation_session_id].model_version_or_snapshot) for s in selected}
    return {"mode": "DEVELOPMENT_ONLY" if synthetic else "ELIGIBLE_DESCRIPTIVE", "sample_count": len(selected),
            "model_count": len(model_keys), "session_count": len({s.generation_session_id for s in selected}),
            "independent_reference_pool_size": 0,
            "canonical_available": len(forms), "unique_forms": len(set(forms)),
            "form_hash_counts": {key: forms.count(key) for key in sorted(set(forms))},
            "message": "合成参考仅用于管线验证，不是真实模型趋同。" if synthetic else
                "仅在本参考集合观察结构模式；会话记录不能认证独立性，不代表真实学生群体。"}


def evidence_card(row, result, reference):
    limits = list(COMMON_LIMITATIONS)
    if reference["mode"] == "UNAVAILABLE":
        limits.append("没有可用的AI参考证据，不生成AI共同模式解释。")
    elif reference["mode"] == "DEVELOPMENT_ONLY":
        limits.append("仅用于界面/管线验证；没有发生真实模型调用。")
    if row["warnings"]:
        limits.append("解析/规范化不可用部分不得作为结构证据。")
    template = next((e.metadata for e in result.evidence if e.metadata.get("category") == "SHARED_TEMPLATE_CONTEXT"), {})
    note = next((e.metadata for e in result.evidence if e.metadata.get("category") == "REVIEW_ASSESSMENT"), {})
    fragment_evidence = next((e for e in result.evidence if e.evidence_type == "TOKEN_MATCH"), None)
    locations = [] if fragment_evidence is None else [{k: v for k, v in f.items() if k != "tokens"}
        for f in fragment_evidence.metadata.get("fragments", [])]
    return {"question_id": row["problem_id"], "comparison_id": row["pair_id"],
        "picas_score": result.weighted_similarity_score, "threshold": result.dynamic_threshold,
        "risk_level": result.risk_level, "risk_margin": result.risk_margin,
        "components": {key: row[key] for key in ("raw", "ast", "canonical", "mapping")},
        "production_metric_weights": {metric.name: metric.weight for metric in result.metrics},
        "component_note": "Standalone parsed diagnostics may remain visible when production fusion falls back; weights above are authoritative.",
        "parse_warnings": row["warnings"], "template_coverage": template,
        "effective_code_length": {side: template.get("submission" + side, {}).get("effectiveTokenCount") for side in ("A", "B")},
        "match_length_distribution": {"status": "UNAVAILABLE", "reason": "Existing evidence is a truncated n-gram location list, not exhaustive maximal matches"},
        "match_locations": locations, "match_locations_exhaustive": False,
        "independent_reference_pool_size": reference["independent_reference_pool_size"],
        "ai_reference_mode": reference["mode"], "common_pattern_summary": reference,
        "provenance_evidence_status": "VERIFIED_RECORDS" if row.get("formal_eligible") else
            "NONE" if reference["mode"] == "DEVELOPMENT_ONLY" else "PARTIAL",
        "provenance_authenticity_certified": False, "assessment": note,
        "limitations": limits, "review_questions": QUESTIONS,
        "source_hashes": {"a": row["code_a_sha256"], "b": row["code_b_sha256"]},
        "production_score_changed": False, "relationship_determined": False}


def preflight_report(question, reference, cards):
    return {"workflow": "ASSIGNMENT_PREFLIGHT", "question_id": question.problem_id,
        "reference": reference, "pair_count": len(cards), "question_confidentiality": question.confidentiality,
        "template_coverage_max": max((card["template_coverage"].get("submission" + side, {}).get("templateCoverage", 0)
            for card in cards for side in ("A", "B")), default=None),
        "warning": "不能依赖最终源码相似度判断个体来源；本报告不预测学生抄袭率。",
        "teaching_options": ["考虑分阶段提交并保留同意范围内的过程记录。", "考虑学生自编测试、解释设计选择或口头复核。"],
        "confidentiality_warning": "未发布题目未经许可不得提交第三方；本原型无网络。",
        "limitations": COMMON_LIMITATIONS, "production_score_changed": False}
