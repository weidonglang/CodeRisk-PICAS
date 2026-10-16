"""Opening-stage formal readiness preflight over the EXISTING dataset protocol.

Read-only: never grants authorization, changes labels, moves splits or marks
humans verified. A stronger preflight, not an alternative dataset schema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research_v4_dataset import (NEGATIVE_LABELS, POSITIVE_LABELS, core_eligibility_issues,
                                  load_research_dataset, _write_csv as write_csv)
from research_protocol import formal_blockers
from similarity_ablation import ROOT, quality_blockers, verify_isolation


REWRITES = {'VARIABLE_RENAME', 'FUNCTION_RENAME', 'PARAMETER_RENAME', 'FORMAT_COMMENT_CHANGE',
            'HUMAN_REWRITE', 'AI_REWRITE', 'CROSSLANG_REWRITE', 'LOCAL_REORDER', 'SPLIT_MERGE', 'ORIGINAL_COPY'}


def case_readiness(case):
    reasons = list(core_eligibility_issues(case))
    # Inspect even excluded cases; an empty eligible set must not masquerade as ready.
    prefix = case['pair_id'] + ': '
    reasons.extend(reason.removeprefix(prefix) for reason in formal_blockers([{**case, 'eligible_for_core_metrics': True}]))
    provenance, annotation = case.get('provenance', {}), case.get('annotation', {})
    provenance = provenance if isinstance(provenance, dict) else {}
    annotation = annotation if isinstance(annotation, dict) else {}
    if provenance.get('functional_check_status') != 'PASSED':
        reasons.append('functional_check_status=PASSED and actual log required')
    if provenance.get('manual_check_status') != 'VERIFIED':
        reasons.append('manual_check_status=VERIFIED required')
    if provenance.get('template_status') not in {'NONE', 'REGISTERED'}:
        reasons.append('shared template context undeclared')
    if provenance.get('template_status') == 'REGISTERED' and not annotation.get('shared_template_ref'):
        reasons.append('registered shared template reference missing')
    if case.get('experiment_label') in NEGATIVE_LABELS:
        if len(set(case.get('source_family_ids', []))) < 2:
            reasons.append('negative pair needs two distinct source families')
        if not isinstance(annotation.get('independence_evidence'), str) or not annotation['independence_evidence'].strip():
            reasons.append('independent-solution relationship evidence missing')
    if case.get('case_type') in REWRITES and not provenance.get('parent_source_ref'):
        reasons.append('known rewrite parent_source_ref missing')
    return sorted(set(reasons))


def assess(manifest, cases, validation, config_bytes):
    sha = hashlib.sha256(config_bytes).hexdigest()
    blockers = list(validation.get('errors', []))
    try:
        groups = verify_isolation(cases)
    except (ValueError, KeyError) as error:
        blockers.append(str(error))
        groups = {}
    blockers.extend(quality_blockers(cases, manifest, sha))
    rows = []
    for case in cases:
        reasons = case_readiness(case)
        selected = bool(case.get('eligible_for_core_metrics'))
        row = {'pair_id': case['pair_id'], 'split': case['split'], 'problem_id': case['problem_id'],
               'source_type': case['source_type'], 'label': case['experiment_label'],
               'selected': selected, 'evidence_ready': not reasons,
               'formal_eligible': selected and not reasons, 'reasons': ' | '.join(reasons)}
        rows.append(row)
        if selected and reasons:
            blockers.append(case['pair_id'] + ': ' + row['reasons'])
    formal = [r for r in rows if r['formal_eligible']]
    for split in ('validation', 'test'):
        pool = [r for r in formal if r['split'] == split]
        if not pool:
            blockers.append(split + ': no reviewed authorized preregistered formal pairs')
        if not any(r['label'] in POSITIVE_LABELS for r in pool) or not any(r['label'] in NEGATIVE_LABELS for r in pool):
            blockers.append(split + ': positive and negative relationship labels required for core comparisons')
    return {'status': 'FORMAL_BLOCKED' if blockers else 'FORMAL_READY_DECLARED_EVIDENCE_REQUIRES_HUMAN_AUDIT',
            'protocolVersion': 'opening-readiness-v1-existing-research-v4-schema',
            'datasetVersion': manifest.get('dataset_version'), 'configSha256': sha,
            'checkedAtUtc': datetime.now(timezone.utc).isoformat(), 'caseCount': len(rows),
            'declaredEligiblePairs': sum(r['selected'] for r in rows),
            'evidenceReadyPairs': sum(r['evidence_ready'] for r in rows),
            'formalEligiblePairs': len(formal) if not blockers else 0,
            'connectedGroups': len(set(groups.values())), 'formalBlockers': sorted(set(blockers)),
            'countsBySourceType': dict(Counter(r['source_type'] for r in rows)), 'rows': rows,
            'meaning': 'Checks declared records and isolation, not truth of consent, human identity, independence or representativeness'}


def run(config_path, output, statistical_config=None):
    output.mkdir(parents=True, exist_ok=False)
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    manifest_path = ROOT / config['datasetManifest']
    manifest, cases, validation = load_research_dataset(manifest_path, raise_on_error=False)
    report = assess(manifest, cases, validation, config_bytes)
    report['manifestSha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if statistical_config is not None:
        from natural_similarity_calibration import load_references, validate_config, validate_reference_isolation
        calibration = json.loads(statistical_config.read_bytes())
        validate_config(calibration)
        _, refs, pools, audit, blockers = load_references(ROOT / calibration['referenceManifest'], calibration)
        queries = []
        for case in cases:
            context = case.get('natural_reference_context') or {}
            queries.append({'problem_id': case['problem_id'], 'split': case['split'],
                'authors': context.get('authors', []), 'sources': context.get('sources', []) + [case['source_id']],
                'families': context.get('families', []) + case.get('source_family_ids', []),
                'hashes': [case['code_a_sha256'], case['code_b_sha256']]})
        try:
            validate_reference_isolation(refs, queries, calibration['referencePolicy'])
        except ValueError as error:
            blockers.append(str(error))
        enough = any(len(pool) >= calibration['minIndependentPairs'] for pool in pools.values())
        report['statisticalReadiness'] = {'status': 'BLOCKED_INSUFFICIENT_INDEPENDENT_REFERENCES' if not enough else
            ('BLOCKED_REFERENCE_PROTOCOL' if blockers else 'REFERENCE_POOLS_AVAILABLE_NO_EFFECT_CLAIM'),
            'trustedReferencePairs': sum(len(p) for p in pools.values()), 'minimumDisjointPairsPerContext': calibration['minIndependentPairs'],
            'referencePolicy': calibration['referencePolicy'], 'blockers': blockers, 'audit': audit,
            'configSha256': hashlib.sha256(statistical_config.read_bytes()).hexdigest()}
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (output / 'dataset_validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_csv(output / 'case_readiness.csv', report['rows'])
    text = ['# Formal readiness preflight', '', '**' + report['status'] + '**', '',
            f"Loaded {report['caseCount']}; evidence ready {report['evidenceReadyPairs']}; formal eligible {report['formalEligiblePairs']}.",
            '', *('- ' + b for b in report['formalBlockers']), '',
            'Passing metadata checks does not authenticate consent or labels. Excluded seed/placeholder rows remain visible.', '']
    (output / 'REPORT.md').write_text('\n'.join(text), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/experiments/similarity_ablation_v1.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--statistical-config', type=Path)
    parser.add_argument('--require-ready', action='store_true', help='Exit 2 if formal comparison OR requested statistical reference audit is blocked')
    args = parser.parse_args()
    report = run(args.config.resolve(), args.output.resolve(), args.statistical_config.resolve() if args.statistical_config else None)
    print(json.dumps({k: report[k] for k in ('status', 'caseCount', 'evidenceReadyPairs', 'formalEligiblePairs')}))
    blocked = report['status'] == 'FORMAL_BLOCKED' or report.get('statisticalReadiness', {}).get('status', '').startswith('BLOCKED')
    raise SystemExit(2 if args.require_ready and blocked else 0)


if __name__ == '__main__':
    main()
