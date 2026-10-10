"""Isolated, frozen multi-signal ablations. Production formulas are never edited."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis-service-python'))
from app.analyzers.problem_profile import FORMULA_VERSION
from app.analyzers.token_similarity import analyze_token_pair, parse_ast_nodes, tokenize_code_with_locations
from identifier_renaming import CASES, permutations, rename
from research_protocol import connected_groups, formal_blockers
from research_v4_dataset import NEGATIVE_LABELS, POSITIVE_LABELS, load_research_dataset
from run_fair_evaluation import metrics as existing_metrics, write_csv, write_json
from run_research_v4 import _request

SIGNALS = {'raw', 'ast', 'canonical', 'mapping'}
LABELS = POSITIVE_LABELS | NEGATIVE_LABELS


def unit(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Finite unit score required')
    return float(value)


def validate_config(config):
    if config['protocolVersion'] != 'similarity-ablation-1.0' or (config['selectionSplit'], config['evaluationSplit']) != ('validation', 'test'):
        raise ValueError('Frozen protocol and validation/test roles required')
    for key, low, high in [('fixedThresholds', 0, 1.000001), ('dynamicOffsets', -.45, .45)]:
        if not config[key] or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not low <= x <= high for x in config[key]):
            raise ValueError('Invalid parameter grid: ' + key)
    unit(config['targetFpr'])
    unit(config['borderlineMargin'])
    if type(config['randomSeed']) is not int or type(config['renameVariantsPerCase']) is not int or not 1 <= config['renameVariantsPerCase'] <= 720:
        raise ValueError('Integer seed and bounded rename count required')
    if not config['retrievalKs'] or any(type(k) is not int or k < 1 for k in config['retrievalKs']):
        raise ValueError('Positive integer retrieval Ks required')
    names = set()
    if not config['methods']:
        raise ValueError('Methods required')
    for method in config['methods']:
        if not isinstance(method['name'], str) or not method['name'] or method['name'] in names:
            raise ValueError('Unique method names required')
        names.add(method['name'])
        if method['thresholdMode'] not in {'FIXED', 'RULE', 'OFFSET'}:
            raise ValueError('Unknown threshold mode')
        if method['scoreMode'] == 'WEIGHTED':
            weights = method.get('weights', {})
            if not weights or not set(weights) <= SIGNALS:
                raise ValueError('Only existing production signals may enter experiments')
            if any(unit(w) <= 0 for w in weights.values()) or not math.isclose(sum(weights.values()), 1, abs_tol=1e-12):
                raise ValueError('Positive fixed weights must sum to one')
        elif method['scoreMode'] != 'PRODUCTION' or 'weights' in method:
            raise ValueError('Production scores must be read, not overridden')


def method_score(row, method):
    if method['scoreMode'] == 'PRODUCTION':
        return unit(row['full']) if row.get('full') is not None else None
    if any(row.get(signal) is None for signal in method['weights']):
        return None
    return sum(unit(row[signal]) * weight for signal, weight in method['weights'].items())


def method_threshold(row, method, parameter):
    if parameter is None:
        return None
    return parameter if method['thresholdMode'] == 'FIXED' else min(.95, max(.50, unit(row['dynamic_threshold']) + parameter))


def binary_metrics(rows, predictions):
    if len(rows) != len(predictions):
        raise ValueError('Prediction count mismatch')
    known = [(row, p) for row, p in zip(rows, predictions) if row['label'] in LABELS and p is not None]
    return existing_metrics([r for r, _ in known], [p for _, p in known])


def average_precision(rows, scores):
    """Non-interpolated PR area (AP), grouping equal-score ties as one threshold."""
    if len(rows) != len(scores):
        raise ValueError('Score count mismatch')
    pairs = [(unit(s), r['label'] in POSITIVE_LABELS) for r, s in zip(rows, scores) if r['label'] in LABELS and s is not None]
    positives = sum(p for _, p in pairs)
    if not positives or positives == len(pairs):
        return None
    grouped = defaultdict(list)
    for score, positive in pairs:
        grouped[score].append(positive)
    tp = seen = 0
    area = 0.0
    for score in sorted(grouped, reverse=True):
        added = sum(grouped[score])
        tp += added
        seen += len(grouped[score])
        area += (added / positives) * (tp / seen)
    return area


def select_operating_point(rows, method, config, target_fpr=None):
    validation = [r for r in rows if r['split'] == 'validation' and r['label'] in LABELS and method_score(r, method) is not None]
    classes = {r['label'] in POSITIVE_LABELS for r in validation}
    base = {'validation_count': len(validation), 'validation_negatives': sum(r['label'] in NEGATIVE_LABELS for r in validation),
            'selection_split': 'validation', 'test_used_for_selection': False, 'parameter': None,
            'validation_fpr': None, 'validation_recall': None}
    if method['thresholdMode'] == 'RULE' and target_fpr is None:
        candidates = [0.0]
    elif classes != {False, True}:
        return {**base, 'status': 'INSUFFICIENT_VALIDATION_CLASSES'}
    else:
        candidates = config['fixedThresholds'] if method['thresholdMode'] == 'FIXED' else [0.0] if method['thresholdMode'] == 'RULE' else config['dynamicOffsets']
    sweep = []
    for parameter in sorted(set(candidates)):
        predicted = [method_score(r, method) >= method_threshold(r, method, parameter) for r in validation]
        result = binary_metrics(validation, predicted)
        if target_fpr is None or result['fpr'] is not None and result['fpr'] <= target_fpr + 1e-12:
            sweep.append({'parameter': parameter, **result})
    if not sweep:
        return {**base, 'status': 'NO_VALIDATION_FPR_POINT'}
    def objective(row):
        primary = row['recall'] if target_fpr is not None else row['f1']
        tie = row['parameter'] if method['thresholdMode'] == 'FIXED' else -abs(row['parameter'])
        return (primary if primary is not None else -1, -(row['fpr'] if row['fpr'] is not None else 1), tie, row['parameter'])
    best = max(sweep, key=objective)
    return {**base, 'status': 'FROZEN_RULE' if method['thresholdMode'] == 'RULE' else 'VALIDATION_SELECTED',
            'parameter': best['parameter'], 'validation_fpr': best['fpr'], 'validation_recall': best['recall']}


def recall_at_k(rows, scores, k):
    if len(rows) != len(scores) or type(k) is not int or k < 1:
        raise ValueError('Matched scores and positive integer k required')
    base = {'k': k, 'value': None, 'queries': 0}
    if not rows or any(not r.get('retrieval_query_id') or r.get('retrieval_pool_complete') is not True
                       or r.get('query_source_sha256') not in {r.get('code_a_sha256'), r.get('code_b_sha256')}
                       or r['label'] not in LABELS or s is None for r, s in zip(rows, scores)):
        return {**base, 'status': 'COMPLETE_LABELED_QUERY_POOL_REQUIRED'}
    groups = defaultdict(list)
    for row, score in zip(rows, scores):
        groups[row['retrieval_query_id']].append((row, unit(score)))
    values = []
    for candidates in groups.values():
        contexts = {(r['problem_id'], r['split'], r['query_source_sha256']) for r, _ in candidates}
        targets = [r['code_b_sha256'] if r['code_a_sha256'] == r['query_source_sha256'] else r['code_a_sha256'] for r, _ in candidates]
        if any(type(r.get('retrieval_pool_size')) is not int or r['retrieval_pool_size'] != len(candidates) for r, _ in candidates):
            return {**base, 'status': 'DECLARED_QUERY_POOL_SIZE_MISMATCH'}
        if len(contexts) != 1 or len(set(targets)) != len(targets):
            return {**base, 'status': 'INCONSISTENT_OR_DUPLICATE_QUERY_POOL'}
        positives = sum(r['label'] in POSITIVE_LABELS for r, _ in candidates)
        if positives:
            ranked = sorted(candidates, key=lambda pair: (-pair[1], pair[0]['pair_id']))
            values.append(sum(r['label'] in POSITIVE_LABELS for r, _ in ranked[:k]) / positives)
    return {'k': k, 'value': sum(values) / len(values) if values else None, 'queries': len(values),
            'status': 'DECLARED_POOL_MACRO_RECALL' if values else 'NO_POSITIVE_QUERY'}


def verify_isolation(cases):
    groups = connected_groups(cases)
    splits = defaultdict(set)
    for case in cases:
        splits[groups[case['pair_id']]].add(case['split'])
    if any(len(partitions) > 1 for partitions in splits.values()):
        raise ValueError('Connected problem/source/family/hash leakage across validation/test')
    return groups


def quality_blockers(cases, manifest, config_sha):
    blockers = formal_blockers(cases)
    for case in cases:
        if not case['eligible_for_core_metrics']:
            continue
        annotation = case.get('annotation', {})
        if not isinstance(annotation, dict) or annotation.get('reviewer_a_type') != 'HUMAN' or annotation.get('reviewer_b_type') != 'HUMAN' or annotation.get('independence_confirmed') is not True:
            blockers.append(case['pair_id'] + ': two independent HUMAN reviews required')
    registration = manifest.get('evaluation_registration', {})
    if not isinstance(registration, dict) or registration.get('status') != 'FROZEN' or registration.get('config_sha256') != config_sha or not registration.get('registered_at') or not registration.get('reference'):
        blockers.append('Frozen dated dataset/config registration required')
    return sorted(set(blockers))


def evaluate(rows, config):
    methods = config['methods']
    common = [r for r in rows if r['label'] in LABELS and all(method_score(r, m) is not None for m in methods)]
    common_ids = {r['pair_id'] for r in common}
    selected, fpr_points, output, predictions, retrieval, coverage = {}, {}, [], [], [], []
    for method in methods:
        name = method['name']
        selected[name] = select_operating_point(common, method, config)
        fpr_points[name] = select_operating_point(common, method, config, config['targetFpr'])
        parameter = selected[name]['parameter']
        for scope, pool in [('COMMON', common), ('AVAILABLE', [r for r in rows if r['label'] in LABELS and method_score(r, method) is not None])]:
            for split in ('validation', 'test'):
                samples = [r for r in pool if r['split'] == split]
                scores = [method_score(r, method) for r in samples]
                thresholds = [method_threshold(r, method, parameter) for r in samples]
                predicted = [s >= t if t is not None else None for s, t in zip(scores, thresholds)]
                margins = [s - t if t is not None else None for s, t in zip(scores, thresholds)]
                # Margins may be negative; AP needs only ordering, so shift them into the unit interval.
                margin_ranks = [(x + 1.000001) / 2.000002 if x is not None else None for x in margins]
                output.append({'method': name, 'scope': scope, 'split': split, 'threshold_status': selected[name]['status'],
                               'parameter': parameter, 'n_ranked': len(samples), **binary_metrics(samples, predicted),
                               'pr_auc_ap_score': average_precision(samples, scores), 'pr_auc_ap_margin': average_precision(samples, margin_ranks)})
        test = [r for r in common if r['split'] == 'test']
        scores = [method_score(r, method) for r in test]
        low_parameter = fpr_points[name]['parameter']
        low_predictions = [s >= method_threshold(r, method, low_parameter) if low_parameter is not None else None for r, s in zip(test, scores)]
        output.append({'method': name, 'scope': 'COMMON_LOW_FPR', 'split': 'test', 'threshold_status': fpr_points[name]['status'],
                       'parameter': low_parameter, 'target_validation_fpr': config['targetFpr'], 'n_ranked': len(test),
                       'validation_negatives': fpr_points[name]['validation_negatives'], **binary_metrics(test, low_predictions)})
        for k in config['retrievalKs']:
            # A matched-support table is not a complete retrieval pool: keep unavailable candidates.
            pool = [r for r in rows if r['split'] == 'test']
            retrieval.append({'method': name, **recall_at_k(pool, [method_score(r, method) for r in pool], k)})
        for row in rows:
            start = time.perf_counter_ns()
            value = method_score(row, method)
            aggregation_us = (time.perf_counter_ns() - start) / 1000
            threshold = method_threshold(row, method, parameter)
            predicted = value >= threshold if value is not None and threshold is not None else None
            known = row['label'] in LABELS
            predictions.append({**{key: row[key] for key in ('pair_id', 'split', 'label', 'problem_id', 'language', 'case_type', 'problem_type', 'group_id')},
                                'method': name, 'score': value, 'threshold': threshold, 'predicted': predicted,
                                'correct': predicted == (row['label'] in POSITIVE_LABELS) if predicted is not None and known else None,
                                'in_common_support': row['pair_id'] in common_ids, 'analysis_elapsed_ms': row['analysis_elapsed_ms'],
                                'aggregation_us': aggregation_us, 'warnings': row['warnings']})
        coverage.append({'method': name, 'requested': len(rows), 'available': sum(method_score(r, method) is not None for r in rows),
                         'common': len(common), 'common_test': len(test)})
    return {'selected': selected, 'low_fpr_selected': fpr_points, 'metrics': output,
            'predictions': predictions, 'retrieval': retrieval, 'coverage': coverage}


def extract_case(case, index, group_id):
    started = time.perf_counter()
    result = analyze_token_pair(_request(index, case, 'PICAS_STANDARD'))
    ast_available = all(parse_ast_nodes(case['code_' + side], case['language_' + side]).parsed
                        and tokenize_code_with_locations(case['code_' + side], case['language_' + side]) for side in ('a', 'b'))
    canonical_available = any(m.name == 'CANONICAL_TOKEN_SIMILARITY' and m.weight > 0 for m in result.metrics)
    elapsed = (time.perf_counter() - started) * 1000
    row = {'pair_id': case['pair_id'], 'split': case['split'], 'label': case['experiment_label'],
           'problem_id': case['problem_id'], 'source_id': case['source_id'], 'group_id': group_id,
           'language': case['language_a'], 'case_type': case['case_type'], 'problem_type': case['problem_type'],
           'raw': result.token_similarity, 'ast': result.ast_similarity if ast_available else None,
           'canonical': result.canonical_token_similarity if canonical_available else None,
           'mapping': result.identifier_mapping_similarity if canonical_available else None,
           'full': result.weighted_similarity_score, 'dynamic_threshold': result.dynamic_threshold,
           'analysis_elapsed_ms': round(elapsed, 6), 'source_type': case['source_type'], 'synthetic': case['synthetic'],
           'code_a_sha256': case['code_a_sha256'], 'code_b_sha256': case['code_b_sha256'],
           'warnings': ' | '.join(e.description for e in result.evidence if e.evidence_type == 'PARSER_WARNING')}
    for key in ('retrieval_query_id', 'retrieval_pool_complete', 'retrieval_pool_size', 'query_source_sha256'):
        if key in case:
            row[key] = case[key]
    return row


def rename_stability(config):
    records = []
    for case in CASES:
        base = {'pair_id': case['id'], 'split': 'validation', 'experiment_label': 'UNCERTAIN',
                'problem_id': case['id'], 'source_id': case['id'], 'source_type': 'synthetic', 'synthetic': True,
                'language_a': case['language'], 'language_b': case['language'], 'case_type': 'SELF_RENAME_PROBE',
                'problem_type': 'correctness_probe', 'question': {'title': 'Rename correctness probe', 'description': 'Self-authored fixed source. Not a benchmark.'},
                'code_a': case['code'], 'code_b': case['code'], 'code_a_sha256': digest(case['code'].encode()), 'code_b_sha256': digest(case['code'].encode())}
        reference = extract_case(base, 1, case['id'])
        for i, mapping in enumerate(permutations(case['domain'], config['renameVariantsPerCase'], config['randomSeed'])):
            transformed = rename(case['code'], case['language'], case['domain'], mapping)
            variant = extract_case({**base, 'code_b': transformed, 'code_b_sha256': digest(transformed.encode())}, 1, case['id'])
            for method in config['methods']:
                before, after = method_score(reference, method), method_score(variant, method)
                records.append({'fixture': case['id'], 'language': case['language'], 'variant': i, 'method': method['name'],
                                'source_type': 'synthetic', 'formal_eligible': False, 'reference_type': 'IDENTICAL_SELF_PAIR',
                                'before_score': before, 'after_score': after, 'delta': after - before if before is not None and after is not None else None,
                                'source_sha256': base['code_a_sha256'], 'variant_sha256': variant['code_b_sha256'],
                                'mapping_json': json.dumps(mapping, sort_keys=True), 'analysis_elapsed_ms': variant['analysis_elapsed_ms']})
    return records


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(config_path, output, allow_development=False):
    if output.exists():
        raise FileExistsError('Immutable run output: use a new directory')
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    validate_config(config)
    manifest_path = ROOT / config['datasetManifest']
    manifest, cases, validation = load_research_dataset(manifest_path)
    groups = verify_isolation(cases)
    blockers = quality_blockers(cases, manifest, digest(config_bytes))
    if blockers and not allow_development:
        raise ValueError('Formal run blocked; --allow-development is exploratory only: ' + '; '.join(blockers[:3]))
    output.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    rows, excluded = [], []
    for i, case in enumerate(cases, 1):
        if not case['eligible_for_core_metrics'] or case['experiment_label'] not in LABELS or case['language_a'] != case['language_b'] or case['language_a'] not in {'java', 'python'}:
            excluded.append({'pair_id': case['pair_id'], 'reason': 'INELIGIBLE_UNKNOWN_LABEL_OR_OUTSIDE_SAME_LANGUAGE_SCOPE'})
            continue
        rows.append(extract_case(case, i, groups[case['pair_id']]))
    result = evaluate(rows, config)
    stability = rename_stability(config)
    write_json(output / 'config.json', config)
    write_json(output / 'dataset_validation.json', validation)
    write_json(output / 'selection.json', {'common_support_only': True, 'test_used_for_selection': False,
                                         'selected': result['selected'], 'low_fpr_selected': result['low_fpr_selected']})
    write_json(output / 'results.json', result)
    for name, data in [('scores', rows), ('excluded', excluded), ('rename_stability', stability), *result.items()]:
        if isinstance(data, list):
            write_csv(output / (name + '.csv'), data)
    failures = [r for r in result['predictions'] if r['split'] == 'test' and r['correct'] is False]
    borderline = [r for r in result['predictions'] if r['split'] == 'test' and r['score'] is not None and r['threshold'] is not None and abs(r['score'] - r['threshold']) <= config['borderlineMargin']]
    write_csv(output / 'failures.csv', failures)
    write_csv(output / 'borderline.csv', borderline)
    write_csv(output / 'parser_fallbacks.csv', [r for r in rows if r['warnings']])
    files = sorted((ROOT / 'analysis-service-python/app').rglob('*.py')) + sorted((ROOT / 'experiment').glob('*.py')) + [ROOT.parent / 'coderisk_docs/FORMULA_SPEC.md']
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    status = subprocess.run(['git', 'status', '--porcelain', '--', 'analysis-service-python', 'experiment', 'configs'], cwd=ROOT, capture_output=True, text=True)
    record = {'status': 'COMPLETED', 'protocolVersion': config['protocolVersion'], 'algorithmVersion': 'SOURCE_HASHES_RECORDED',
              'formulaVersion': FORMULA_VERSION, 'datasetVersion': manifest['dataset_version'], 'randomSeed': config['randomSeed'],
              'runId': output.name, 'gitCommit': git.stdout.strip(), 'sourceWorkingTreeDirty': bool(status.stdout.strip()),
              'sourceHashes': {p.relative_to(ROOT.parent).as_posix(): digest(p.read_bytes()) for p in files},
              'configSha256': digest(config_bytes), 'manifestSha256': digest(manifest_path.read_bytes()),
              'datasetSha256': digest(json.dumps(cases, sort_keys=True, ensure_ascii=True).encode()),
              'startedAtUtc': started, 'completedAtUtc': datetime.now(timezone.utc).isoformat(),
              'elapsedSeconds': time.perf_counter() - clock, 'python': platform.python_version(),
              'claimLevel': 'DEVELOPMENT_EXPLORATORY_NOT_BENCHMARK' if allow_development else 'FROZEN_REVIEWED_DATASET_OBSERVATION',
              'formalEligiblePairs': 0 if allow_development else len(rows), 'formalBlockers': blockers,
              'inputCases': len(cases), 'analyzedPairs': len(rows), 'excludedPairs': len(excluded),
              'productionFormulaChanged': False, 'jplagStatus': 'NOT_RUN_NO_HISTORICAL_SCORE_MERGE'}
    write_json(output / 'run_manifest.json', record)
    report = ['# Frozen similarity ablation', '', '**' + record['claimLevel'] + '**', '',
              'Existing same-language Java/Python features only. No production weighting or thresholds changed.', '',
              '| Method | Common test N | Precision | Recall | F1 | FPR | Natural FPR | PR area (AP score) |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    fmt = lambda x: 'N/A' if x is None else f'{x:.4f}'
    for row in result['metrics']:
        if row['scope'] == 'COMMON' and row['split'] == 'test':
            report.append('| ' + row['method'] + ' | ' + str(row['n_ranked']) + ' | ' + ' | '.join(fmt(row[k]) for k in ('precision', 'recall', 'f1', 'fpr', 'natural_fpr', 'pr_auc_ap_score')) + ' |')
    report += ['', 'COMMON is the primary matched-support table; AVAILABLE is diagnostic only and must not be compared as equal coverage.',
               'PR area is non-interpolated AP with tied scores grouped; it is not trapezoidal PR integration. Single-class/unknown labels are N/A.',
               'LOW_FPR uses only validation to choose a feasible operating point. Report achieved test FPR, not a guaranteed population FPR.',
               'Recall@K needs a declared complete labeled query pool; arbitrary sampled pairs cannot support retrieval recall.',
               'Rename probes compare identical self pairs with legal renamed variants. They test score sensitivity, not accuracy or semantic equivalence.',
               'Analysis time includes shared feature extraction and availability checks. Aggregation time excludes shared extraction; not a per-algorithm benchmark.',
               'This run does not rescore ConPlag, retune its inspected test set, or merge historical JPlag outputs with new algorithm scores.',
               'The historical Full-not-highest-F1 observation remains unchanged. Statistical independent-solution calibration and LLM baselines are not implemented here.', '']
    (output / 'REPORT.md').write_text('\n'.join(report), encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/experiments/similarity_ablation_v1.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-development', action='store_true', help='Unverified/synthetic exploratory data only, formal eligible count is zero')
    args = parser.parse_args()
    result = run(args.config.resolve(), args.output.resolve(), args.allow_development)
    print(json.dumps({k: result[k] for k in ('status', 'claimLevel', 'runId', 'analyzedPairs', 'formalEligiblePairs')}))


if __name__ == '__main__':
    main()
