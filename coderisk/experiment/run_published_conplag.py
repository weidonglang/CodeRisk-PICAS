"""Frozen exploratory evaluation against published ConPlag labels, separate from core-study eligibility."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
import importlib.metadata
import json
import math
from pathlib import Path
import random
import sys

from acquire_public_datasets import digest, verify_intake, write_json, write_rows
from review_public_data import ROOT, jsonl, source_bytes
from research_v4_jplag import DEFAULT_JAR, DEFAULT_JAVA, execute_jplag

sys.path.insert(0, str(ROOT / 'analysis-service-python'))
from app.analyzers import token_similarity as analysis
from app.analyzers.canonicalization import canonicalize_code, build_identifier_mapping

METHODS = ('FULL_FIXED', 'NO_CANONICAL_FIXED', 'RAW_FIXED', 'CANONICAL_FIXED')


@lru_cache(maxsize=4096)
def features(code):
    tokens = analysis.tokenize_code_with_locations(code, 'java')
    ast = analysis.parse_ast_nodes(code, 'java')
    canonical = canonicalize_code(code, 'java', tokens)
    return tokens, analysis._fingerprints([t.value for t in tokens]), ast, canonical


def pair_scores(left, right):
    a, fingerprints_a, ast_a, can_a = features(left)
    b, fingerprints_b, ast_b, can_b = features(right)
    raw = analysis._jaccard(fingerprints_a, fingerprints_b) if a and b else 0.0
    ast_enabled = bool(a and b and ast_a.parsed and ast_b.parsed)
    fusion = ast_enabled and can_a.mode != 'lexical-fallback' and can_b.mode != 'lexical-fallback'
    ast_score = analysis._sequence_similarity([n.value for n in ast_a.nodes], [n.value for n in ast_b.nodes]) if ast_enabled else 0.0
    canonical = analysis._sequence_similarity(can_a.tokens, can_b.tokens) if fusion else 0.0
    mapping = build_identifier_mapping(can_a, can_b).similarity if fusion else 0.0
    full = analysis._weighted_similarity(raw, ast_score, canonical, mapping, ast_enabled, fusion)
    scores = {'FULL_FIXED': full, 'NO_CANONICAL_FIXED': .5 * raw + .5 * ast_score if fusion else raw,
            'RAW_FIXED': raw, 'CANONICAL_FIXED': canonical if fusion else raw,
            'raw': raw, 'ast': ast_score, 'canonical': canonical, 'mapping': mapping, 'fusion_enabled': fusion,
            'canonical_mode_a': can_a.mode, 'canonical_mode_b': can_b.mode}
    return {key: round(value, 6) if type(value) is float else value for key, value in scores.items()}


def published_metrics(rows, method, threshold):
    tp = fp = tn = fn = 0
    for row in rows:
        if row['published_verdict'] not in (0, 1) or not math.isfinite(row[method]) or not 0 <= row[method] <= 1:
            raise ValueError('Binary published labels and finite unit scores required')
        positive, predicted = row['published_verdict'] == 1, row[method] >= threshold
        tp += int(positive and predicted)
        fn += int(positive and not predicted)
        fp += int(not positive and predicted)
        tn += int(not positive and not predicted)
    ratio = lambda a, b: a / b if b else None
    return {'n': len(rows), 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
            'precision': ratio(tp, tp + fp), 'recall': ratio(tp, tp + fn),
            'f1': ratio(2 * tp, 2 * tp + fp + fn), 'fpr': ratio(fp, fp + tn)}


def calibrate(rows, method, candidates):
    if not candidates or any(not math.isfinite(t) or not 0 <= t <= 1 for t in candidates):
        raise ValueError('Finite nonempty unit threshold grid required')
    validation = [r for r in rows if r['split'] == 'validation']
    if {r['published_verdict'] for r in validation} != {0, 1}:
        raise ValueError('Both published classes required in validation')
    sweep = [{'threshold': t, **published_metrics(validation, method, t)} for t in candidates]
    best = max(sweep, key=lambda r: (r['f1'], -r['fpr'], r['threshold']))
    return best['threshold'], sweep


def verify_no_overlap(pairs, assignments):
    if len(assignments) != len(pairs) or {p['pair_id'] for p in pairs} != set(assignments):
        raise ValueError('Every published pair needs exactly one split assignment')
    observed = defaultdict(set)
    for pair in pairs:
        split = assignments[pair['pair_id']]['proposed_split']
        if split not in {'validation', 'test'}:
            raise ValueError('Invalid partition')
        keys = [('problem', pair['problem_id'])] + [('family', f) for f in pair['source_family_ids']]
        keys += [('text-hash', f['code_sha256_text']) for files in pair['files'].values() for f in files]
        for key in keys:
            observed[key].add(split)
    overlap = [key for key, splits in observed.items() if len(splits) > 1]
    if overlap:
        raise ValueError('Cross-partition overlap: ' + repr(overlap[:5]))
    return {'problem_family_raw_and_template_free_text_hash_overlaps': 0,
            'author_identity_available': False, 'author_isolation_claimed': False}


def prepare(intake, output):
    verify_intake(intake)
    pairs = jsonl(intake / 'conplag-v3/published_pairs.jsonl')
    proposal = json.loads((intake / 'conplag-v3/split_proposal.json').read_text(encoding='utf-8'))
    assignments = {r['pair_id']: r for r in proposal['rows']}
    overlap = verify_no_overlap(pairs, assignments)
    output.mkdir(parents=True)
    write_rows(output / 'published_pairs_snapshot.jsonl', pairs)
    write_json(output / 'split_assignments.json', assignments)
    paths = [Path(__file__), ROOT / 'experiment/research_v4_jplag.py',
             ROOT / 'experiment/review_public_data.py', ROOT / 'experiment/acquire_public_datasets.py']
    paths.extend(sorted((ROOT / 'analysis-service-python/app/analyzers').glob('*.py')))
    implementation = {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in paths}
    protocol = {'status': 'FROZEN_EXPLORATORY_PUBLISHED_LABEL_PROTOCOL', 'client_date': '2026-10-09',
                'registered_at_utc': datetime.now(timezone.utc).isoformat(), 'pair_scores_computed_before_freeze': False,
                'intake_registry_sha256': digest((intake / 'source_registry.json').read_bytes()),
                'pair_snapshot_sha256': digest((output / 'published_pairs_snapshot.jsonl').read_bytes()),
                'split_assignments_sha256': digest((output / 'split_assignments.json').read_bytes()),
                'pair_count': len(pairs), 'published_class_counts': dict(Counter(p['published_verdict'] for p in pairs)),
                'split_counts': dict(Counter(r['proposed_split'] for r in assignments.values())), 'overlap_check': overlap,
                'views': ['version_1', 'version_2'], 'views_are_paired_not_extra_samples': True,
                'methods': list(METHODS), 'fixed_threshold_candidates': [i / 20 for i in range(1, 21)],
                'threshold_selection': 'validation F1, lower FPR, higher threshold; test labels never select parameters',
                'jplag': {'version': '6.2.0', 'min_tokens': 5, 'jar_sha256': digest(DEFAULT_JAR.read_bytes())},
                'bootstrap': {'groups': 'published problem', 'repetitions': 1000, 'seed': 20261009},
                'dynamic_threshold_evaluated': False, 'natural_similarity_fpr_evaluated': False,
                'reason': 'Problem descriptions/profiles and natural-independent labels unavailable in ConPlag intake.',
                'label_scope': 'Published single-annotator labels; no local double review; not disciplinary ground truth.',
                'formal_core_eligible_pairs': 0, 'downloaded_sources_executed': False,
                'common_cohort': 'Only emitted native JPlag comparisons; missing values remain unknown. Also report PICAS all-pair results.',
                'implementation_sha256': implementation}
    protocol['score_precision'] = '6 decimals, consistent with production API; ablations rounded after combination'
    protocol['runtime'] = {'python': sys.version.split()[0],
                           'tree-sitter': importlib.metadata.version('tree-sitter')}
    write_json(output / 'protocol.json', protocol)
    print(json.dumps({'output': str(output), 'pair_count': len(pairs), 'split_counts': protocol['split_counts']}))


def bootstrap(rows, parameters, config):
    groups = defaultdict(list)
    for row in rows:
        groups[row['problem_id']].append(row)
    keys = sorted(groups)
    rng, values = random.Random(config['seed']), defaultdict(list)
    for _ in range(config['repetitions']):
        sample = [r for _ in keys for r in groups[rng.choice(keys)]]
        for method, threshold in parameters.items():
            for metric, value in published_metrics(sample, method, threshold).items():
                if metric in {'f1', 'recall', 'fpr'} and value is not None:
                    values[(method, metric)].append(value)
    return [{'method': method, 'metric': metric, 'groups': len(keys), 'valid_replicates': len(observed),
             'low': sorted(observed)[math.floor((len(observed)-1)*.025)],
             'high': sorted(observed)[math.ceil((len(observed)-1)*.975)]} for (method, metric), observed in values.items()]


def evaluate(rows, cohort, methods, protocol):
    if {r['published_verdict'] for r in rows if r['split'] == 'validation'} != {0, 1} or not any(r['split'] == 'test' for r in rows):
        return {'status': 'INSUFFICIENT_COHORT', 'parameters': {}, 'tables': [], 'validation_sweeps': [],
                'test_cluster_intervals': [], 'reason': 'Both validation classes and at least one test case required'}
    parameters, sweeps, tables = {}, [], []
    for method in methods:
        parameters[method], sweep = calibrate(rows, method, protocol['fixed_threshold_candidates'])
        sweeps.extend({'cohort': cohort, 'method': method, **r} for r in sweep)
        for split in ('validation', 'test'):
            tables.append({'cohort': cohort, 'method': method, 'split': split, 'threshold': parameters[method],
                           **published_metrics([r for r in rows if r['split'] == split], method, parameters[method])})
    test = [r for r in rows if r['split'] == 'test']
    intervals = bootstrap(test, parameters, protocol['bootstrap']) if len({r['problem_id'] for r in test}) >= 2 else []
    return {'status': 'EVALUATED', 'parameters': parameters, 'tables': tables, 'validation_sweeps': sweeps, 'test_cluster_intervals': intervals}


def run(intake, registration, output, jar, java):
    protocol = json.loads((registration / 'protocol.json').read_text(encoding='utf-8'))
    for key, file in [('pair_snapshot_sha256', 'published_pairs_snapshot.jsonl'), ('split_assignments_sha256', 'split_assignments.json')]:
        if digest((registration / file).read_bytes()) != protocol[key]:
            raise ValueError('Registration changed')
    for path, expected in protocol['implementation_sha256'].items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError('Registered implementation changed: ' + path)
    if digest(jar.read_bytes()) != protocol['jplag']['jar_sha256']:
        raise ValueError('JPlag jar changed')
    for package in ('tree-sitter',):
        if importlib.metadata.version(package) != protocol['runtime'][package]:
            raise ValueError('Registered dependency changed: ' + package)
    if sys.version.split()[0] != protocol['runtime']['python']:
        raise ValueError('Registered Python version changed')
    if digest((intake / 'source_registry.json').read_bytes()) != protocol['intake_registry_sha256']:
        raise ValueError('Intake registry changed')
    verify_intake(intake)
    pairs = jsonl(registration / 'published_pairs_snapshot.jsonl')
    assignments = json.loads((registration / 'split_assignments.json').read_text(encoding='utf-8'))
    verify_no_overlap(pairs, assignments)
    output.mkdir(parents=True)
    write_json(output / 'protocol_snapshot.json', protocol)
    write_json(output / 'run_start.json', {'status': 'RUNNING_EXPLORATORY_ONLY', 'protocol_sha256': digest((registration / 'protocol.json').read_bytes())})
    summaries = {}
    for view in protocol['views']:
        view_output = output / view
        view_output.mkdir()
        rows, jplag_groups = [], defaultdict(list)
        for index, pair in enumerate(pairs):
            files = pair['files'][view]
            codes = [source_bytes(intake / 'conplag-v3', f['code_path'], f['code_sha256_bytes'])[1].decode('utf-8') for f in files]
            row = {'pair_id': pair['pair_id'], 'problem_id': pair['problem_id'], 'published_verdict': pair['published_verdict'],
                   'split': assignments[pair['pair_id']]['proposed_split'], 'view': view, 'eligible_for_core_metrics': False,
                   **pair_scores(*codes)}
            rows.append(row)
            ids = [f['submission_id'] + '-' + f['code_sha256_bytes'][:16] for f in files]
            problem_output = view_output / 'jplag' / pair['problem_id'].rsplit(':', 1)[-1]
            for code, sid in zip(codes, ids):
                target = problem_output / 'input/java' / sid / 'Main.java'
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and target.read_text(encoding='utf-8') != code:
                    raise ValueError('JPlag source collision')
                target.write_text(code, encoding='utf-8')
            jplag_groups[pair['problem_id']].append({'pairId': pair['pair_id'], 'language': 'java',
                'submissionA': ids[0], 'submissionB': ids[1], 'publishedVerdict': pair['published_verdict']})
            if (index + 1) % 100 == 0:
                print(f'{view}: scored {index + 1}/{len(pairs)}', flush=True)
        write_rows(view_output / 'picas_scores.jsonl', rows)
        baselines, native_runs = [], []
        for problem, aligned in sorted(jplag_groups.items()):
            print(f'{view}: JPlag {problem}', flush=True)
            current, runs = execute_jplag(view_output / 'jplag' / problem.rsplit(':', 1)[-1], aligned,
                                          jar, java, protocol['jplag']['version'], protocol['jplag']['min_tokens'])
            baselines.extend(current)
            native_runs.extend({'problem_id': problem, **r} for r in runs)
        write_rows(view_output / 'jplag_scores.jsonl', baselines)
        write_json(view_output / 'jplag_runs.json', native_runs)
        baseline = {r['pairId']: r for r in baselines}
        common = [{**r, 'JPLAG_FIXED': baseline[r['pair_id']]['predictedScore']} for r in rows
                  if baseline[r['pair_id']]['resultStatus'] == 'MATCHED']
        all_result = evaluate(rows, 'PICAS_ALL_PUBLISHED_PAIRS', METHODS, protocol)
        common_result = evaluate(common, 'JPLAG_MATCHED_COMMON_COHORT', (*METHODS, 'JPLAG_FIXED'), protocol) if common else None
        exclusions = [{'pair_id': r['pairId'], 'published_verdict': r['publishedVerdict'],
                       'status': r['resultStatus'], 'reason': r['reason']} for r in baselines if r['resultStatus'] != 'MATCHED']
        write_json(view_output / 'evaluation.json', {'all_picas_pairs': all_result, 'common_cohort': common_result, 'exclusions': exclusions})
        summaries[view] = {'pair_count': len(rows), 'jplag_matched_pairs': len(common), 'jplag_missing_pairs': len(exclusions),
                           'all_picas_test_tables': [r for r in all_result['tables'] if r['split'] == 'test'],
                           'common_test_tables': [r for r in common_result['tables'] if r['split'] == 'test'] if common_result else []}
    write_json(output / 'run_summary.json', {'status': 'EXPLORATORY_EXTERNAL_LABEL_RESULTS', 'client_date': '2026-10-09',
               'protocol_sha256': digest((registration / 'protocol.json').read_bytes()), 'views': summaries,
               'not_formal_core_evaluation': True, 'dynamic_threshold_claims_supported': False,
               'downloaded_code_executed': False, 'test_used_for_threshold_selection': False,
               'runtime': {'python': sys.version.split()[0], 'tree-sitter': importlib.metadata.version('tree-sitter')}})
    print(json.dumps({'output': str(output), 'status': 'EXPLORATORY_EXTERNAL_LABEL_RESULTS'}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--intake', type=Path, default=ROOT / 'data/public-datasets/public-intake-20261008')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--registration', type=Path)
    parser.add_argument('--jplag-jar', type=Path, default=DEFAULT_JAR)
    parser.add_argument('--java', type=Path, default=DEFAULT_JAVA)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output directory')
    if args.prepare:
        prepare(args.intake, args.output)
    else:
        if not args.registration:
            parser.error('--registration required')
        try:
            run(args.intake, args.registration, args.output, args.jplag_jar.resolve(), args.java.resolve())
        except Exception as error:
            if args.output.is_dir():
                write_json(args.output / 'RUN_FAILED.json', {'status': 'FAILED', 'error': type(error).__name__, 'message': str(error)})
            raise


if __name__ == '__main__':
    main()
