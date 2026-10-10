"""Gated offline PICAS candidates -> model evidence -> human review experiment."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import time

from llm_baseline import (ROOT, Review, aggregate, build_request, canonical_json, digest,
    import_records, process_requests, validate_config, verify_permission, write_jsonl)
from natural_similarity_calibration import extract_query
from similarity_ablation import (LABELS, FORMULA_VERSION, binary_metrics, load_research_dataset,
    quality_blockers, recall_at_k, select_operating_point, unit, verify_isolation, write_csv, write_json)


def validate_hybrid_config(config):
    if config['protocolVersion'] != 'hybrid-review-1.0' or (config['selectionSplit'], config['evaluationSplit']) != ('validation', 'test'):
        raise ValueError('Frozen hybrid protocol with validation-only selection required')
    if not config['candidateKs'] or any(type(k) is not int or not 1 <= k <= 10000 for k in config['candidateKs']):
        raise ValueError('Positive bounded candidate Ks required')
    unit(config['targetCandidateRecall'])
    if config['targetCandidateRecall'] <= 0 or any(type(config[k]) is not int or config[k] < 1 for k in ('minimumValidationPositiveQueries', 'minimumBaselineTestPairs', 'randomSeed')):
        raise ValueError('Positive recall target, query/baseline minima and seed required')
    validate_config(config['llm'])
    if config['llm']['promptVersion'] != 'hybrid-review-1.0' or config['llm']['promptFile'] != 'experiment/prompts/hybrid_review_v1.txt':
        raise ValueError('Separate versioned hybrid prompt required')


def audit_pools(rows):
    reasons, groups, pair_ids = [], defaultdict(list), set()
    for row in rows:
        pair_id = row['pair_id']
        if pair_id in pair_ids:
            reasons.append({'pair_id': pair_id, 'reason': 'DUPLICATE_PAIR_ID'})
        pair_ids.add(pair_id)
        query = row.get('retrieval_query_id')
        if not isinstance(query, str) or not query.strip() or row.get('retrieval_pool_complete') is not True or row.get('query_source_sha256') not in {row.get('code_a_sha256'), row.get('code_b_sha256')}:
            reasons.append({'pair_id': pair_id, 'reason': 'COMPLETE_ANCHORED_QUERY_POOL_REQUIRED'})
            continue
        groups[query].append(row)
        try:
            unit(row['full'])
            unit(row['dynamic_threshold'])
        except (ValueError, KeyError, TypeError):
            reasons.append({'pair_id': pair_id, 'reason': 'PRODUCTION_SCORE_REQUIRED_INCLUDING_FALLBACK'})
        if row['label'] not in LABELS or row['split'] not in {'validation', 'test'} or not row.get('question_context_sha256'):
            reasons.append({'pair_id': pair_id, 'reason': 'KNOWN_LABEL_SPLIT_AND_CONTEXT_REQUIRED'})
    for query, candidates in groups.items():
        contexts = {(r['problem_id'], r['split'], r['query_source_sha256'], r.get('language'), r.get('question_context_sha256'), r['dynamic_threshold']) for r in candidates}
        targets = [r['code_b_sha256'] if r['code_a_sha256'] == r['query_source_sha256'] else r['code_a_sha256'] for r in candidates]
        if len(contexts) != 1 or len(set(targets)) != len(targets) or any(target == candidates[0]['query_source_sha256'] for target in targets):
            reasons.append({'pair_id': query, 'reason': 'INCONSISTENT_CONTEXT_DUPLICATE_OR_SELF_TARGET'})
        if any(type(r.get('retrieval_pool_size')) is not int or r['retrieval_pool_size'] != len(candidates) for r in candidates):
            reasons.append({'pair_id': query, 'reason': 'DECLARED_POOL_SIZE_MISMATCH'})
    if not rows:
        reasons.append({'pair_id': '', 'reason': 'NO_QUERY_POOL'})
    return {'valid': not reasons, 'queries': len(groups), 'pairs': len(rows), 'reasons': reasons}


def select_candidates(rows, k):
    if type(k) is not int or k < 1 or not audit_pools(rows)['valid']:
        raise ValueError('Valid complete pools and positive k required')
    groups = defaultdict(list)
    for row in rows:
        groups[row['retrieval_query_id']].append(row)
    return [row for query in sorted(groups) for row in sorted(groups[query],
        key=lambda r: (-(r['full'] - r['dynamic_threshold']), -r['full'], r['pair_id']))[:k]]


def candidate_recall(rows, k):
    if not audit_pools(rows)['valid']:
        return {'k': k, 'value': None, 'queries': 0, 'status': 'COMPLETE_LABELED_QUERY_POOL_REQUIRED'}
    return recall_at_k(rows, [(r['full'] - r['dynamic_threshold'] + 1) / 2 for r in rows], k)


def choose_k(rows, config):
    validation = [r for r in rows if r['split'] == 'validation']
    points = [candidate_recall(validation, k) for k in sorted(set(config['candidateKs']))]
    acceptable = [p for p in points if p['value'] is not None and p['queries'] >= config['minimumValidationPositiveQueries'] and p['value'] >= config['targetCandidateRecall']]
    return {'k': acceptable[0]['k'] if acceptable else None, 'selectedOn': 'validation',
        'status': 'VALIDATION_RECALL_POINT' if acceptable else 'NO_VALIDATION_RECALL_POINT', 'points': points}


def verify_baseline(directory, review_path, dataset_sha, config):
    result = {'ready': False, 'reason': 'RELIABLE_REVIEWED_REAL_BASELINE_REQUIRED'}
    if directory is None or review_path is None:
        return result
    import csv
    path = directory / 'run_manifest.json'
    record, review = json.loads(path.read_bytes()), json.loads(review_path.read_bytes())
    if not isinstance(record, dict) or not isinstance(review, dict):
        return result
    approved = review.get('status') == 'APPROVED' and review.get('reviewer_type') == 'HUMAN' and review.get('recommended_for_hybrid') is True and all(isinstance(review.get(k), str) and review[k].strip() for k in ('reviewer_id', 'reference')) and review.get('reviewed_run_manifest_sha256') == digest(path.read_bytes())
    if not approved or record.get('mode') != 'import' or record.get('claimLevel') != 'FROZEN_REVIEWED_IMPORTED_OBSERVATION' or record.get('formalBlockers') or record.get('formalEligiblePairs', 0) < config['minimumBaselineTestPairs'] or record.get('realModelResponses', 0) < 1 or record.get('testUsedForSelection') is not False or record.get('datasetSha256') != dataset_sha or record.get('modelId') != config['llm']['modelId'] or record.get('modelParameters') != config['llm']['modelParameters']:
        return result
    hashes = record.get('sourceHashes') or {}
    production = sorted((ROOT / 'analysis-service-python/app').rglob('*.py')) + [ROOT.parent / 'coderisk_docs/FORMULA_SPEC.md']
    if any(hashes.get(p.relative_to(ROOT.parent).as_posix()) != digest(p.read_bytes()) for p in production):
        return {**result, 'reason': 'BASELINE_PRODUCTION_SOURCE_MISMATCH'}
    with (directory / 'metrics.csv').open(encoding='utf-8-sig', newline='') as handle:
        metrics = list(csv.DictReader(handle))
    comparison = [m for m in metrics if m['scope'] == 'COMMON_THREE' and m['split'] == 'test' and int(m['n']) >= config['minimumBaselineTestPairs']]
    if {m['method'] for m in comparison} != {'PICAS_FIXED', 'PICAS_RULE_DYNAMIC', 'JPLAG', 'DIRECT_LLM'}:
        return {**result, 'reason': 'MATCHED_REAL_BASELINE_COVERAGE_REQUIRED'}
    return {'ready': True, 'reason': 'HUMAN_APPROVED_LOCAL_ARTIFACT_NOT_EXTERNAL_ATTESTATION',
        'manifestSha256': digest(path.read_bytes()), 'reviewSha256': digest(review_path.read_bytes())}


def make_request(case, row, config, repetition):
    context = {'weightedSimilarityScore': row['full'], 'dynamicThreshold': row['dynamic_threshold'],
        'riskMargin': row['full'] - row['dynamic_threshold'], 'rawTokenSimilarity': row['raw'] if 'raw' in row else None,
        'astSimilarity': row.get('ast'), 'canonicalTokenSimilarity': row.get('canonical'),
        'identifierMappingSimilarity': row.get('mapping'), 'warning': row.get('warnings', ''),
        'instruction': 'Hints are not labels or relationship evidence; verify original sources.'}
    return build_request(case, config, repetition, context)


def evaluate_pipeline(rows, selected_ids, config):
    if not audit_pools(rows)['valid'] or not selected_ids <= {r['pair_id'] for r in rows}:
        raise ValueError('Complete known pool and valid selected identities required')
    base = {'metrics': [], 'selection': None, 'semantics': 'REVIEW_QUEUE_FLAG_NOT_RELATION_JUDGMENT'}
    selected = [r for r in rows if r['pair_id'] in selected_ids]
    if not selected or any(r.get('llm') is None for r in selected):
        return {**base, 'status': 'SELECTED_REVIEWS_INCOMPLETE'}
    point = select_operating_point([{**r, 'full': r['llm']} for r in selected],
        {'name': 'HYBRID_REVIEW_QUEUE', 'scoreMode': 'PRODUCTION', 'thresholdMode': 'FIXED'}, config['llm'])
    if point['parameter'] is None:
        return {**base, 'status': 'NO_VALIDATION_OPERATING_POINT'}
    metrics = []
    for split in ('validation', 'test'):
        pool = [r for r in rows if r['split'] == split]
        predicted = [r['llm'] >= point['parameter'] if r['pair_id'] in selected_ids else False for r in pool]
        metrics.append({'split': split, **binary_metrics(pool, predicted)})
    return {**base, 'status': 'ALL_POOL_REVIEW_QUEUE_METRICS', 'selection': point, 'metrics': metrics}


def run(config_path, output, mode='mock', allow_development=False, responses=None,
        cache_dir=None, baseline_dir=None, baseline_review=None, export_prompts=False):
    if output.exists():
        raise FileExistsError('Immutable output directory required')
    started, timer = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    data = config_path.read_bytes()
    config = json.loads(data)
    validate_hybrid_config(config)
    if mode not in {'mock', 'dry-run', 'import'} or responses and mode != 'import':
        raise ValueError('Only offline modes and matching import inputs allowed')
    manifest, cases, validation = load_research_dataset(ROOT / config['datasetManifest'])
    groups = verify_isolation(cases)
    dataset_sha = digest(canonical_json(cases).encode())
    blockers = quality_blockers(cases, manifest, digest(data))
    registration = manifest.get('evaluation_registration') or {}
    frozen = {'prompt_sha256': digest((ROOT / config['llm']['promptFile']).read_bytes()),
        'schema_sha256': digest(canonical_json(Review.model_json_schema()).encode()), 'dataset_sha256': dataset_sha}
    if any(registration.get(k) != value for k, value in frozen.items()):
        blockers.append('Hybrid prompt/schema/dataset preregistration required')
    baseline = verify_baseline(baseline_dir, baseline_review, dataset_sha, config)
    if not allow_development and (blockers or mode != 'import' or not baseline['ready']):
        raise ValueError('Formal hybrid needs frozen reviewed data and reliable real baseline')
    rows, excluded, by_id = [], [], {}
    for index, case in enumerate(cases, 1):
        if not case['eligible_for_core_metrics'] or case['experiment_label'] not in LABELS or case['language_a'] != case['language_b'] or case['language_a'] not in {'java', 'python'}:
            excluded.append({'pair_id': case['pair_id'], 'reason': 'OUTSIDE_SAME_LANGUAGE_KNOWN_LABEL_SCOPE', 'declared_query': case.get('retrieval_query_id', '')})
            continue
        row = extract_query(case, index, groups[case['pair_id']])
        row.update(code_a_sha256=case['code_a_sha256'], code_b_sha256=case['code_b_sha256'], llm=None,
            question_context_sha256=digest(canonical_json({'question': case['question'], 'background': case.get('natural_reference_context')}).encode()))
        for key in ('retrieval_query_id', 'retrieval_pool_complete', 'retrieval_pool_size', 'query_source_sha256'):
            if key in case:
                row[key] = case[key]
        rows.append(row)
        by_id[case['pair_id']] = case
    audit = audit_pools(rows)
    if any(r['declared_query'] for r in excluded):
        audit['valid'] = False
        audit['reasons'].append({'pair_id': '', 'reason': 'EXCLUDED_DECLARED_POOL_MEMBER_DO_NOT_SHRINK_POOL'})
    point = choose_k(rows, config) if audit['valid'] else {'k': None, 'points': [], 'selectedOn': 'validation', 'status': 'BLOCKED_INCOMPLETE_QUERY_POOLS'}
    status = 'BLOCKED_INCOMPLETE_QUERY_POOLS' if not audit['valid'] else 'BLOCKED_NO_VALIDATION_RECALL_POINT' if point['k'] is None else 'BLOCKED_REAL_BASELINE_REQUIRED' if mode == 'import' and not baseline['ready'] else 'DEVELOPMENT_CANDIDATE_WORKFLOW_ONLY' if mode != 'import' else 'IMPORTED_HYBRID_OBSERVATION_HUMAN_REVIEW_REQUIRED'
    permitted = status in {'DEVELOPMENT_CANDIDATE_WORKFLOW_ONLY', 'IMPORTED_HYBRID_OBSERVATION_HUMAN_REVIEW_REQUIRED'}
    selected = select_candidates(rows, point['k']) if permitted else []
    selected_ids = {r['pair_id'] for r in selected}
    if mode == 'import' and permitted and ('MOCK' in config['llm']['modelId'] or 'FILL_' in config['llm']['modelId']):
        raise ValueError('Exact non-placeholder model identifier required')
    plans = [(make_request(by_id[r['pair_id']], r, config['llm'], repetition), by_id[r['pair_id']])
        for r in selected if verify_permission(by_id[r['pair_id']]) for repetition in range(config['llm']['repeats'])]
    entries = import_records(responses) if responses else {}
    if set(entries) - {r['requestSha256'] for r, _ in plans}:
        raise ValueError('Unknown hybrid response identity or blocked pipeline')
    reviews, usage = process_requests(plans, config['llm'], mode, entries, cache_dir)
    for review, (_, case) in zip(reviews, plans):
        review['pair_id'] = case['pair_id']
    queue = []
    for row in rows:
        row.update(aggregate([r for r in reviews if r['pair_id'] == row['pair_id']], config['llm']))
        queue.append({'pair_id': row['pair_id'], 'split': row['split'], 'query_id': row.get('retrieval_query_id', ''),
            'candidateStatus': 'SELECTED' if row['pair_id'] in selected_ids else 'NOT_SELECTED_UNASSESSED' if permitted else 'PIPELINE_BLOCKED',
            'modelReviewStatus': 'STRUCTURED_MODEL_RESPONSE_HUMAN_VERIFICATION_REQUIRED' if row['llm'] is not None else 'UNAVAILABLE',
            'modelOutcomes': '|'.join(sorted({r['output']['outcome'] for r in reviews if r['pair_id'] == row['pair_id'] and r['output']})),
            'humanReviewStatus': 'REQUIRED' if row['pair_id'] in selected_ids else 'NOT_ASSESSED', 'score': row['llm']})
    result = evaluate_pipeline(rows, selected_ids, config) if mode == 'import' and permitted else {'status': 'NO_REAL_MODEL_METRICS', 'metrics': [], 'selection': None}
    recall = [{'split': split, **candidate_recall([r for r in rows if r['split'] == split], k)} for split in ('validation', 'test') for k in config['candidateKs']]
    output.mkdir(parents=True)
    for name, payload in [('config', config), ('dataset_validation', validation), ('pool_audit', audit), ('selection', point), ('pipeline_evaluation', result)]:
        write_json(output / (name + '.json'), payload)
    for name, records in [('human_review_queue', queue), ('pool_failures', audit['reasons']), ('excluded', excluded), ('candidate_recall', recall), ('pipeline_metrics', result['metrics'])]:
        write_csv(output / (name + '.csv'), records)
    write_jsonl(output / 'scores.jsonl', rows)
    write_jsonl(output / 'model_outputs.jsonl', reviews)
    write_jsonl(output / 'requests.jsonl', [{'pair_id': case['pair_id'], **{k: req[k] for k in ('requestSha256', 'repetition', 'modelId', 'modelParameters', 'promptVersion')}} for req, case in plans])
    write_jsonl(output / 'responses_template.jsonl', [{**{k: req[k] for k in ('requestSha256', 'repetition', 'modelId', 'modelParameters', 'promptVersion')}, 'latencyMs': None, 'costUsd': None, 'usage': None, 'output': None} for req, _ in plans])
    if export_prompts:
        write_jsonl(output / 'prompts.jsonl', [req for req, _ in plans])
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, capture_output=True, text=True)
    files = sorted((ROOT / 'analysis-service-python/app').rglob('*.py')) + sorted((ROOT / 'experiment').glob('*.py')) + [ROOT / config['llm']['promptFile'], ROOT.parent / 'coderisk_docs/FORMULA_SPEC.md']
    record = {'status': status, 'claimLevel': 'DEVELOPMENT_NOT_BENCHMARK' if allow_development else 'FROZEN_REVIEWED_IMPORTED_OBSERVATION',
        'protocolVersion': config['protocolVersion'], 'formulaVersion': FORMULA_VERSION, 'algorithmVersion': 'SOURCE_HASHES_RECORDED',
        'datasetVersion': manifest['dataset_version'], 'datasetSha256': dataset_sha, 'configSha256': digest(data),
        'sourceHashes': {p.relative_to(ROOT.parent).as_posix(): digest(p.read_bytes()) for p in files},
        'responseFileSha256': digest(responses.read_bytes()) if responses else None,
        'schemaSha256': digest(canonical_json(Review.model_json_schema()).encode()),
        'runId': output.name, 'mode': mode, 'modelId': config['llm']['modelId'], 'modelParameters': config['llm']['modelParameters'],
        'promptVersion': config['llm']['promptVersion'], 'randomSeed': config['randomSeed'], 'gitCommit': git.stdout.strip(),
        'workingTreeDirty': bool(dirty.stdout.strip()), 'python': platform.python_version(),
        'baselineGate': baseline, 'formalBlockers': blockers, 'formalEligiblePairs': 0 if allow_development or not permitted else len(rows),
        'inputPairs': len(cases), 'analyzedPairs': len(rows), 'excludedPairs': len(excluded), 'completePoolQueries': audit['queries'] if audit['valid'] else 0,
        'selectedK': point['k'], 'selectedPairs': len(selected), 'realModelResponses': len({r['requestSha256'] for r in reviews if r['status'] in {'IMPORTED', 'CACHE_HIT'}}),
        'testUsedForSelection': False, 'productionFormulaChanged': False, **usage,
        'startedAtUtc': started, 'completedAtUtc': datetime.now(timezone.utc).isoformat(), 'elapsedSeconds': time.perf_counter() - timer}
    write_json(output / 'run_manifest.json', record)
    report = ['# Offline hybrid candidate review', '', '**' + record['claimLevel'] + '**', '', 'Status: ' + status,
        f"Pairs: {len(rows)}; complete queries: {record['completePoolQueries']}; selected K: {point['k']}; selected: {len(selected)}.",
        'Candidate K is selected on validation only. Recall is macro recall over positive queries in the declared finite pool, not a population guarantee.',
        'Missing/unsupported candidates must not be dropped. Non-selected means unassessed, never independent.',
        'Mock/dry-run have no model metrics. Real import needs a reviewed matched baseline, complete pools and authorized sources.',
        'End-to-end review-queue metrics include every pool member, including candidate-stage misses. Located quotes do not validate reasoning.',
        'No network calls, source execution, paid inference or production changes. Final judgment requires human review.', '',
        '| Split | K | Positive queries | Recall@K | Status |', '| --- | ---: | ---: | ---: | --- |']
    for item in recall:
        report.append(f"| {item['split']} | {item['k']} | {item['queries']} | {item['value'] if item['value'] is not None else 'N/A'} | {item['status']} |")
    (output / 'REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/experiments/hybrid_review_v1.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['mock', 'dry-run', 'import'], default='mock')
    parser.add_argument('--allow-development', action='store_true')
    for name in ('responses', 'cache-dir', 'baseline-dir', 'baseline-review'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--export-prompts', action='store_true')
    args = parser.parse_args()
    result = run(args.config.resolve(), args.output.resolve(), args.mode, args.allow_development,
        args.responses.resolve() if args.responses else None, args.cache_dir.resolve() if args.cache_dir else None,
        args.baseline_dir.resolve() if args.baseline_dir else None, args.baseline_review.resolve() if args.baseline_review else None, args.export_prompts)
    print(json.dumps({k: result[k] for k in ('status', 'analyzedPairs', 'selectedK', 'selectedPairs', 'realModelResponses', 'newNetworkCalls', 'newCostUsd')}))


if __name__ == '__main__':
    main()
