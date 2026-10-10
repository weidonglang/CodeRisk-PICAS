"""Offline independent-solution upper-tail experiment; no production score changes."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import time

from similarity_ablation import (ROOT, LABELS, FORMULA_VERSION, POSITIVE_LABELS, analyze_token_pair,
    binary_metrics, digest, load_research_dataset, quality_blockers, select_operating_point,
    unit, verify_isolation, write_csv, write_json, _request)

IDENTITIES = ('authors', 'sources', 'families', 'hashes')
POLICIES = {'VALIDATION_PROBLEMS_ONLY', 'PREREGISTERED_CONTEXT_PANEL'}


def validate_config(config):
    if config['protocolVersion'] != 'natural-calibration-1.0' or config['referencePolicy'] not in POLICIES:
        raise ValueError('Unsupported frozen calibration protocol')
    if (config['selectionSplit'], config['evaluationSplit']) != ('validation', 'test'):
        raise ValueError('Validation-only selection and frozen test evaluation required')
    for key in ('minIndependentPairs', 'minEffectiveTokens'):
        if type(config[key]) is not int or config[key] < 1:
            raise ValueError('Positive integer required: ' + key)
    if type(config['randomSeed']) is not int:
        raise ValueError('Integer randomSeed required')
    for key in ('maxTemplateCoverage', 'borderlineMargin'):
        unit(config[key])
    if not config['alphaCandidates'] or any(not 0 < unit(x) < 1 for x in config['alphaCandidates']):
        raise ValueError('Nonempty finite alpha grid in (0,1) required')
    if not config['fixedThresholds'] or any(isinstance(x, bool) or not isinstance(x, (int, float))
        or not 0 <= x <= 1.000001 for x in config['fixedThresholds']):
        raise ValueError('Finite fixed threshold grid required')


def empirical_tail(scores, target):
    target = unit(target)
    values = [unit(s) for s in scores]
    count = sum(s >= target for s in values)
    n = len(values)
    return {'reference_n': n, 'tail_count': count, 'q_empirical': count / n if n else None,
            'q_smoothed': (1 + count) / (1 + n) if n else None,
            'resolution': 1 / (1 + n) if n else None}


def identities(row):
    return {(key, value.strip()) for key in IDENTITIES for value in
            (row.get(key, []) if isinstance(row.get(key, []), list) else []) if isinstance(value, str) and value.strip()}


def declared_pair(row, key, distinct=False):
    values = row.get(key)
    return isinstance(values, list) and len(values) == 2 and all(isinstance(v, str) and v.strip() for v in values) and (not distinct or len({v.strip() for v in values}) == 2)


def disjoint_pairs(rows, seed):
    # Seeded ID order is independent of similarity scores and incoming file order.
    ordered = sorted(rows, key=lambda r: (digest(f"{seed}:{r['reference_id']}".encode()), r['reference_id']))
    kept, dropped, seen = [], [], set()
    for row in ordered:
        keys = identities(row)
        if seen & keys:
            dropped.append({'reference_id': row['reference_id'], 'reason': 'REUSED_AUTHOR_SOURCE_FAMILY_OR_HASH'})
        else:
            kept.append(row)
            seen |= keys
    return kept, dropped


def reference_issues(record):
    reasons = []
    if record.get('source_type') not in {'manual', 'external'} or record.get('synthetic') is not False:
        reasons.append('NON_REAL_OR_UNSUPPORTED_REFERENCE_SOURCE')
    if not all(declared_pair(record, k, True) for k in ('authors', 'sources', 'families')):
        reasons.append('DISTINCT_REFERENCE_IDENTITIES_REQUIRED')
    review = record.get('review') or {}
    required = ('reviewer_a', 'reviewer_b', 'label_basis', 'reviewed_at', 'functional_evidence')
    if not isinstance(review, dict) or review.get('status') != 'AGREED' or review.get('label') != 'INDEPENDENT' or any(
        not isinstance(review.get(k), str) or not review[k].strip() for k in required) or review['reviewer_a'].strip() == review['reviewer_b'].strip() or any(
        review.get(k) != 'HUMAN' for k in ('reviewer_a_type', 'reviewer_b_type')) or review.get('independence_confirmed') is not True or review.get('relation_verified') is not True:
        reasons.append('INDEPENDENT_HUMAN_RELATION_REVIEW_REQUIRED')
    provenance = record.get('provenance') or {}
    if not isinstance(provenance, dict) or any(not isinstance(provenance.get(k), str) or not provenance[k].strip()
        for k in ('license_or_authorization', 'source_reference')):
        reasons.append('AUTHORIZATION_AND_SOURCE_REQUIRED')
    if record.get('language') not in {'java', 'python'} or not record.get('problem_id') or not record.get('reference_id'):
        reasons.append('REFERENCE_SCOPE_OR_ID_INVALID')
    return reasons


def validate_reference_isolation(references, queries, policy):
    if policy not in POLICIES:
        raise ValueError('Unknown reference policy')
    query_ids = set().union(*(identities(r) for r in queries)) if queries else set()
    if any(identities(r) & query_ids for r in references):
        raise ValueError('Reference/query author/source/family/hash leakage')
    partitions = {split: set().union(*(identities(r) for r in queries if r['split'] == split))
                  for split in ('validation', 'test')}
    if partitions['validation'] & partitions['test']:
        raise ValueError('Validation/test query identity leakage')
    validation = {r['problem_id'] for r in queries if r['split'] == 'validation'}
    test = {r['problem_id'] for r in queries if r['split'] == 'test'}
    panels = {split: set().union(*(identities(r) for r in references if r['problem_id'] in problems))
              for split, problems in [('validation', validation), ('test', test)]}
    if panels['validation'] & panels['test']:
        raise ValueError('Validation/test reference panel identity leakage')
    if policy == 'VALIDATION_PROBLEMS_ONLY':
        if any(r['problem_id'] not in validation or r['problem_id'] in test for r in references):
            raise ValueError('References must belong only to validation problems; test cold start required')


def query_tail(row, pools, config):
    reasons = []
    if config['referencePolicy'] == 'VALIDATION_PROBLEMS_ONLY' and row['split'] == 'test':
        reasons.append('PROBLEM_DISJOINT_TEST_COLD_START')
    if not row.get('canonical_available'):
        reasons.append('PARSER_OR_NORMALIZATION_FALLBACK')
    if not all(declared_pair(row, k) for k in IDENTITIES):
        reasons.append('QUERY_IDENTITIES_UNDECLARED')
    if not row.get('context_key'):
        reasons.append('TEMPLATE_CONTEXT_UNDECLARED')
    if row.get('effective_tokens', 0) < config['minEffectiveTokens']:
        reasons.append('SHORT_EFFECTIVE_CODE')
    if row.get('template_coverage', 1) >= config['maxTemplateCoverage']:
        reasons.append('TEMPLATE_DOMINATED')
    pool = pools.get((row['problem_id'], row['language'], row.get('context_key')), [])
    if not pool:
        reasons.append('COLD_START_NO_MATCHED_REFERENCE')
    elif len(pool) < config['minIndependentPairs']:
        reasons.append('INSUFFICIENT_DISJOINT_REFERENCE_PAIRS')
    if reasons:
        return {'q_available': False, 'q_empirical': None, 'q_smoothed': None, 'tail_count': None,
                'resolution': 1 / (1 + len(pool)) if pool else None, 'reference_n': len(pool), 'reasons': reasons}
    return {**empirical_tail([r['score'] for r in pool], row['full']), 'q_available': True, 'reasons': []}


def statistical_prediction(row, alpha):
    if alpha is not None and row.get('q_available'):
        return unit(row['q_smoothed']) <= alpha
    return unit(row['full']) >= unit(row['dynamic_threshold'])


def select_alpha(rows, config):
    validation = [r for r in rows if r['split'] == 'validation' and r['label'] in LABELS]
    supported = [r for r in validation if r.get('q_available')]
    base = {'selection_split': 'validation', 'test_used_for_selection': False, 'alpha': None,
            'validation_count': len(validation), 'calibratable_validation_count': len(supported), 'sweep': []}
    if {r['label'] in POSITIVE_LABELS for r in supported} != {False, True}:
        return {**base, 'status': 'INSUFFICIENT_CALIBRATABLE_VALIDATION_CLASSES'}
    sweep = [{'alpha': a, **binary_metrics(validation, [statistical_prediction(r, a) for r in validation])}
             for a in sorted(set(config['alphaCandidates']))]
    best = max(sweep, key=lambda r: (r['f1'] if r['f1'] is not None else -1, -(r['fpr'] if r['fpr'] is not None else 1), -r['alpha']))
    return {**base, 'alpha': best['alpha'], 'status': 'VALIDATION_SELECTED', 'sweep': sweep}


def compare_policies(rows, config):
    fixed = select_operating_point(rows, {'name': 'FIXED', 'scoreMode': 'PRODUCTION', 'thresholdMode': 'FIXED'}, config)
    selection = select_alpha(rows, config)
    alpha, threshold = selection['alpha'], fixed['parameter']
    predictions = []
    for row in rows:
        reasons = list(row.get('reasons', []))
        if alpha is None:
            reasons.append('VALIDATION_ALPHA_UNAVAILABLE')
        predictions.append({**{k: row[k] for k in ('pair_id', 'problem_id', 'split', 'label')},
            'score': row['full'], 'dynamic_threshold': row['dynamic_threshold'], 'fixed_threshold': threshold,
            'alpha': alpha, 'q_smoothed': row.get('q_smoothed'), 'q_available': row.get('q_available', False),
            'fixed_predicted': row['full'] >= threshold if threshold is not None else None,
            'rule_predicted': row['full'] >= row['dynamic_threshold'],
            'statistical_predicted': statistical_prediction(row, alpha),
            'decision_source': 'INDEPENDENT_TAIL' if alpha is not None and row.get('q_available') else 'RULE_FALLBACK',
            'fallback_reasons': ' | '.join(reasons)})
    metrics = []
    for scope in ('ALL_TEST_POLICY', 'CALIBRATABLE_ONLY'):
        for split in ('validation', 'test'):
            indices = [i for i, r in enumerate(rows) if r['split'] == split and
                       (scope == 'ALL_TEST_POLICY' or alpha is not None and r.get('q_available'))]
            samples = [rows[i] for i in indices]
            for method, field in [('FIXED', 'fixed_predicted'), ('RULE_DYNAMIC', 'rule_predicted'),
                                  ('STATISTICAL_WITH_RULE_FALLBACK', 'statistical_predicted')]:
                result = binary_metrics(samples, [predictions[i][field] for i in indices])
                suspicious = [i for i in indices if rows[i]['label'] == 'SUSPICIOUS' and predictions[i][field] is not None]
                metrics.append({'method': method, 'scope': scope, 'split': split, **result,
                    'suspicious_n': len(suspicious), 'suspicious_recall': sum(predictions[i][field] for i in suspicious) / len(suspicious) if suspicious else None,
                    'calibratable_n': sum(rows[i].get('q_available', False) for i in indices)})
    return {'fixed_selection': fixed, 'alpha_selection': selection, 'metrics': metrics, 'predictions': predictions}


def template_key(context, language):
    if context.get('template_status') == 'NONE' and not context.get('template_code'):
        return 'NONE'
    if context.get('template_status') == 'REGISTERED' and context.get('template_language') == language and all(
        isinstance(context.get(k), str) and context[k].strip() for k in ('template_code', 'template_source')):
        return 'TEMPLATE:' + digest(context['template_code'].encode())
    return None


def extract_query(case, index, group_id):
    context = case.get('natural_reference_context') or {}
    if not isinstance(context, dict):
        context = {}
    key = template_key(context, case['language_a'])
    request = _request(index, case, 'PICAS_STANDARD')
    if key and key != 'NONE':
        request.question = type(request.question).model_validate({**request.question.model_dump(by_alias=True),
            'starterCode': context['template_code'], 'starterLanguage': context['template_language'], 'starterSource': context['template_source']})
    started = time.perf_counter()
    result = analyze_token_pair(request)
    shared = next(e.metadata for e in result.evidence if e.metadata.get('category') == 'SHARED_TEMPLATE_CONTEXT')
    compatibility = next(e.metadata for e in result.evidence if e.metadata.get('category') == 'LANGUAGE_COMPATIBILITY')
    canonical = any(m.name == 'CANONICAL_TOKEN_SIMILARITY' and m.weight > 0 for m in result.metrics)
    ast_available = all(compatibility[s]['syntaxParsed'] and shared[s]['tokenCount'] for s in ('submissionA', 'submissionB'))
    return {'pair_id': case['pair_id'], 'problem_id': case['problem_id'], 'split': case['split'],
        'label': case['experiment_label'], 'language': case['language_a'], 'group_id': group_id,
        'case_type': case['case_type'], 'problem_type': case['problem_type'], 'source_type': case['source_type'],
        'synthetic': case['synthetic'], 'full': result.weighted_similarity_score, 'dynamic_threshold': result.dynamic_threshold,
        'raw': result.token_similarity, 'ast': result.ast_similarity if ast_available else None,
        'canonical': result.canonical_token_similarity if canonical else None,
        'mapping': result.identifier_mapping_similarity if canonical else None, 'canonical_available': canonical,
        'context_key': key, 'effective_tokens': min(shared[s]['effectiveTokenCount'] for s in ('submissionA', 'submissionB')),
        'template_coverage': max(shared[s]['templateCoverage'] for s in ('submissionA', 'submissionB')),
        **{k: context.get(k, []) for k in ('authors', 'sources', 'families')},
        'hashes': [case['code_a_sha256'], case['code_b_sha256']],
        'analysis_elapsed_ms': round((time.perf_counter() - started) * 1000, 6),
        'warnings': ' | '.join(e.description for e in result.evidence if e.evidence_type == 'PARSER_WARNING')}


def registration_issues(manifest):
    registration = manifest.get('registration') or {}
    reason = ['REFERENCE_PANEL_NOT_FROZEN_WITH_DATED_EVIDENCE_AND_HASH']
    if not isinstance(registration, dict):
        return reason
    expected = digest(json.dumps(manifest['records'], sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode())
    try:
        dated = datetime.fromisoformat(registration.get('registered_at', '')).utcoffset() is not None
    except (ValueError, TypeError):
        dated = False
    if not isinstance(registration, dict) or registration.get('status') != 'FROZEN' or not dated or registration.get('records_sha256') != expected or registration.get('frozen_before_test_access') is not True or not registration.get('evidence_reference'):
        return reason
    return []


def load_references(path, config):
    manifest = json.loads(path.read_bytes())
    if manifest.get('schema_version') != 'independent-reference-1.0' or not isinstance(manifest.get('records'), list):
        raise ValueError('Invalid independent reference manifest')
    common = registration_issues(manifest)
    references, audit, seen = [], [], set()
    for i, record in enumerate(manifest['records'], 1):
        ref_id = record.get('reference_id', '')
        if not ref_id or ref_id in seen:
            raise ValueError('Unique nonempty reference_id required')
        seen.add(ref_id)
        reasons = list(common) + reference_issues(record)
        if record.get('active') is not True:
            reasons.append('INACTIVE_REFERENCE')
        codes, hashes, byte_hashes = [], [], []
        for side in ('a', 'b'):
            name = record.get('code_' + side + '_path')
            file = (path.parent / name).resolve() if isinstance(name, str) and name else None
            if file is None or not file.is_relative_to(path.parent.resolve()) or not file.is_file():
                reasons.append('REFERENCE_PATH_MISSING_OR_OUTSIDE_MANIFEST_ROOT')
                continue
            data = file.read_bytes()
            byte_hashes.append(digest(data))
            if digest(data) != record.get('code_' + side + '_sha256'):
                reasons.append('REFERENCE_HASH_MISMATCH')
            try:
                # Match Research V4's UTF-8 universal-newline text hash namespace.
                code = file.read_text(encoding='utf-8')
                codes.append(code)
                hashes.append('sha256:' + digest(code.encode()))
            except UnicodeError:
                reasons.append('REFERENCE_UTF8_REQUIRED')
        row = {**record, 'hashes': hashes, 'byte_hashes': byte_hashes, 'score': None, 'context_key': template_key(record, record.get('language'))}
        if not row['context_key']:
            reasons.append('TEMPLATE_CONTEXT_UNDECLARED')
        if not reasons:
            case = {'pair_id': ref_id, 'problem_id': record['problem_id'], 'split': 'validation', 'experiment_label': 'INDEPENDENT',
                'language_a': record['language'], 'language_b': record['language'], 'code_a': codes[0], 'code_b': codes[1],
                'code_a_sha256': hashes[0], 'code_b_sha256': hashes[1], 'source_type': record['source_type'], 'synthetic': False,
                'case_type': 'INDEPENDENT_REFERENCE', 'problem_type': 'reference', 'question': record.get('question', {}),
                'natural_reference_context': record}
            try:
                extracted = extract_query(case, i, 'reference')
                row.update(score=extracted['full'])
                if not extracted['canonical_available']:
                    reasons.append('PARSER_OR_NORMALIZATION_FALLBACK')
                if extracted['effective_tokens'] < config['minEffectiveTokens']:
                    reasons.append('SHORT_EFFECTIVE_CODE')
                if extracted['template_coverage'] >= config['maxTemplateCoverage']:
                    reasons.append('TEMPLATE_DOMINATED')
            except (KeyError, ValueError) as error:
                reasons.append('INVALID_REFERENCE_QUESTION_OR_TEMPLATE: ' + str(error))
        row['trusted'] = not reasons
        references.append(row)
        audit.append({'reference_id': ref_id, 'problem_id': record.get('problem_id'), 'language': record.get('language'),
                      'trusted': not reasons, 'score': row['score'], 'code_text_hashes': hashes, 'source_byte_hashes': byte_hashes,
                      'reasons': ' | '.join(sorted(set(reasons)))})
    grouped = defaultdict(list)
    for row in references:
        if row['trusted']:
            grouped[(row['problem_id'], row['language'], row['context_key'])].append(row)
    pools = {}
    for key, rows in grouped.items():
        pools[key], dropped = disjoint_pairs(rows, config['randomSeed'])
        for removal in dropped:
            next(r for r in audit if r['reference_id'] == removal['reference_id']).update(trusted=False, reasons=removal['reason'])
    return manifest, references, pools, audit, common


def run(config_path, output, allow_development=False):
    if output.exists():
        raise FileExistsError('Immutable run output: use a new directory')
    started, clock = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    validate_config(config)
    manifest_path, reference_path = (ROOT / config[k] for k in ('datasetManifest', 'referenceManifest'))
    manifest, cases, validation = load_research_dataset(manifest_path)
    groups = verify_isolation(cases)
    blockers = quality_blockers(cases, manifest, digest(config_bytes))
    reference_manifest, references, pools, audit, reference_blockers = load_references(reference_path, config)
    blockers += reference_blockers
    if not any(pools.values()):
        blockers.append('No trusted disjoint independent reference pairs')
    if blockers and not allow_development:
        raise ValueError('Formal run blocked; --allow-development cannot relax reference gates: ' + '; '.join(blockers[:3]))
    rows, excluded = [], []
    for i, case in enumerate(cases, 1):
        if not case['eligible_for_core_metrics'] or case['experiment_label'] not in LABELS or case['language_a'] != case['language_b'] or case['language_a'] not in {'java', 'python'}:
            excluded.append({'pair_id': case['pair_id'], 'reason': 'INELIGIBLE_LABEL_OR_OUTSIDE_SAME_LANGUAGE_SCOPE'})
        else:
            rows.append(extract_query(case, i, groups[case['pair_id']]))
    # Check even quarantined references. Development mode never waives known leakage.
    all_queries = []
    for case in cases:
        context = case.get('natural_reference_context') or {}
        all_queries.append({'problem_id': case['problem_id'], 'split': case['split'],
            **{k: context.get(k, []) if isinstance(context, dict) else [] for k in ('authors', 'sources', 'families')},
            'hashes': [case['code_a_sha256'], case['code_b_sha256']]})
        all_queries[-1]['sources'] = (all_queries[-1]['sources'] if isinstance(all_queries[-1]['sources'], list) else []) + [case['source_id']]
        all_queries[-1]['families'] = (all_queries[-1]['families'] if isinstance(all_queries[-1]['families'], list) else []) + case.get('source_family_ids', [])
    validate_reference_isolation(references, all_queries, config['referencePolicy'])
    for row in rows:
        row.update(query_tail(row, pools, config))
    result = compare_policies(rows, config)
    if not allow_development and result['alpha_selection']['alpha'] is None:
        raise ValueError('Formal run blocked: calibratable validation positives and negatives required')
    output.mkdir(parents=True)
    write_json(output / 'config.json', config)
    write_json(output / 'dataset_validation.json', validation)
    write_json(output / 'results.json', result)
    write_json(output / 'selection.json', {'fixed': result['fixed_selection'], 'alpha': result['alpha_selection'], 'test_used_for_selection': False})
    for name, data in [('queries', rows), ('reference_audit', audit), ('excluded', excluded), ('metrics', result['metrics']), ('predictions', result['predictions'])]:
        write_csv(output / (name + '.csv'), data)
    write_csv(output / 'failures.csv', [{**p, 'method': m} for p in result['predictions'] if p['split'] == 'test'
        for m, field in [('FIXED', 'fixed_predicted'), ('RULE_DYNAMIC', 'rule_predicted'), ('STATISTICAL_WITH_RULE_FALLBACK', 'statistical_predicted')]
        if p[field] is not None and p[field] != (p['label'] in POSITIVE_LABELS)])
    write_csv(output / 'borderline.csv', [p for p in result['predictions'] if p['split'] == 'test' and
        (abs(p['score'] - p['dynamic_threshold']) <= config['borderlineMargin'] or
         p['q_smoothed'] is not None and p['alpha'] is not None and abs(p['q_smoothed'] - p['alpha']) <= config['borderlineMargin'])])
    write_csv(output / 'parser_fallbacks.csv', [r for r in rows if r['warnings'] or not r['canonical_available']])
    write_json(output / 'mathematical_contracts.json', {'source_type': 'MATHEMATICAL_CONTRACT_NOT_CODE_METRICS',
        'scores': [.1, .4, .4, .8], 'target': .4, **empirical_tail([.1, .4, .4, .8], .4)})
    files = sorted((ROOT / 'analysis-service-python/app').rglob('*.py')) + sorted((ROOT / 'experiment').glob('*.py')) + [ROOT.parent / 'coderisk_docs/FORMULA_SPEC.md']
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'analysis-service-python', 'experiment', 'configs'], cwd=ROOT, capture_output=True, text=True)
    count = sum(r['q_available'] for r in rows)
    record = {'status': 'COMPLETED_DEVELOPMENT_NO_STATISTICAL_EFFECT_CLAIM' if allow_development else 'COMPLETED_FROZEN_REVIEWED_OBSERVATION',
        'claimLevel': 'DEVELOPMENT_EXPLORATORY_NOT_BENCHMARK' if allow_development else 'FROZEN_REVIEWED_DATASET_OBSERVATION',
        'protocolVersion': config['protocolVersion'], 'referencePolicy': config['referencePolicy'],
        'referenceTestProblemDisjoint': config['referencePolicy'] == 'VALIDATION_PROBLEMS_ONLY',
        'formulaVersion': FORMULA_VERSION, 'algorithmVersion': 'SOURCE_HASHES_RECORDED', 'datasetVersion': manifest['dataset_version'],
        'referenceDatasetVersion': reference_manifest['dataset_version'], 'randomSeed': config['randomSeed'], 'runId': output.name,
        'gitCommit': git.stdout.strip(), 'sourceWorkingTreeDirty': bool(dirty.stdout.strip()),
        'sourceHashes': {p.relative_to(ROOT.parent).as_posix(): digest(p.read_bytes()) for p in files},
        'configSha256': digest(config_bytes), 'manifestSha256': digest(manifest_path.read_bytes()), 'referenceManifestSha256': digest(reference_path.read_bytes()),
        'datasetSha256': digest(json.dumps(cases, sort_keys=True, ensure_ascii=True).encode()),
        'startedAtUtc': started, 'completedAtUtc': datetime.now(timezone.utc).isoformat(), 'elapsedSeconds': time.perf_counter() - clock,
        'python': platform.python_version(), 'inputCases': len(cases), 'analyzedPairs': len(rows), 'excludedPairs': len(excluded),
        'trustedReferencePairs': sum(len(p) for p in pools.values()), 'calibratableQueries': count,
        'formalEligiblePairs': 0 if allow_development else len(rows), 'formalBlockers': blockers,
        'referenceAudit': audit, 'productionFormulaChanged': False, 'externalBaselineStatus': 'NOT_RUN_NO_HISTORICAL_MERGE'}
    write_json(output / 'run_manifest.json', record)
    report = ['# Independent-solution statistical calibration', '', '**' + record['claimLevel'] + '**', '',
        'q is an upper-tail frequency among reviewed independent solutions, NOT a plagiarism probability.',
        'Scores and rule thresholds are read from PICAS_STANDARD unchanged; V4 production weights remain zero.',
        f"Reference protocol: {config['referencePolicy']}. Trusted disjoint pairs: {record['trustedReferencePairs']}. Queries with q: {count}.",
        '', '| Method | Test N | Precision | Recall | F1 | FPR | Natural FPR |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    fmt = lambda x: 'N/A' if x is None else f'{x:.4f}'
    for row in result['metrics']:
        if row['scope'] == 'ALL_TEST_POLICY' and row['split'] == 'test':
            report.append('| ' + row['method'] + ' | ' + str(row['n']) + ' | ' + ' | '.join(fmt(row[k]) for k in ('precision', 'recall', 'f1', 'fpr', 'natural_fpr')) + ' |')
    report += ['', 'ALL_TEST_POLICY is the primary same-query policy comparison (also exports validation diagnostics). CALIBRATABLE_ONLY is supplementary matched support.',
        'Statistical decisions use q_smoothed <= alpha; all unavailable q or unavailable validation alpha use RULE_FALLBACK, not fixed fallback.',
        'If all queries fall back, the statistical policy is exactly the rule policy: this is NOT evidence of statistical calibration benefit.',
        'Default problem-disjoint testing is new-problem cold start. PREREGISTERED_CONTEXT_PANEL permits same-problem reference context and must NOT be called reference/test problem-disjoint.',
        'Greedy author/source/family/hash-disjoint matching limits code-pair reuse, but does not prove IID/exchangeability or remove cohort bias.',
        'The +1 smoothed tail is a conservative empirical estimate, not a guaranteed calibrated p-value, confidence interval, or semantic equivalence test.',
        'Missing authors, relation reviews, authorization, template declaration, sufficient reference size, supported parsing, or effective length cause explicit unavailability.',
        'Short/template-dominated solutions are declined; the scaffold does NOT demonstrate reduced false positives in those settings.',
        'No test tuning, student code execution, external upload, LLM calls, or merged historical JPlag results. Synthetic seed runs support only workflow checks.', '']
    (output / 'REPORT.md').write_text('\n'.join(report), encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/experiments/natural_calibration_v1.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-development', action='store_true', help='Exploratory only; does not waive reference quality or leakage gates')
    args = parser.parse_args()
    result = run(args.config.resolve(), args.output.resolve(), args.allow_development)
    print(json.dumps({k: result[k] for k in ('status', 'runId', 'trustedReferencePairs', 'calibratableQueries', 'formalEligiblePairs')}))


if __name__ == '__main__':
    main()
