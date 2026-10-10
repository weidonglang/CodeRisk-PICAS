"""Offline Direct LLM comparison: mock, dry-run or authorized JSONL import only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import platform
from pathlib import Path
import statistics
import subprocess
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt
from natural_similarity_calibration import extract_query
from similarity_ablation import (ROOT, LABELS, POSITIVE_LABELS, FORMULA_VERSION, binary_metrics,
    digest, load_research_dataset, quality_blockers, select_operating_point, unit,
    verify_isolation, write_csv, write_json)

SCHEMA_VERSION = 'llm-risk-review-1.0'
MODES = {'mock', 'dry-run', 'import'}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class Span(StrictModel):
    startLine: StrictInt = Field(ge=1)
    endLine: StrictInt = Field(ge=1)
    quote: str = Field(min_length=1, max_length=1000)


class Finding(StrictModel):
    codeA: Span
    codeB: Span
    reason: str = Field(min_length=1, max_length=1000)


class Review(StrictModel):
    schemaVersion: Literal['llm-risk-review-1.0']
    outcome: Literal['REVIEW_SIGNAL', 'NO_REVIEW_SIGNAL', 'ABSTAIN']
    riskScore: float | None = Field(ge=0, le=1)
    summary: str = Field(min_length=1, max_length=2000)
    evidence: list[Finding] = Field(max_length=20)
    limitations: list[str] = Field(min_length=1, max_length=10)


class Usage(StrictModel):
    inputTokens: StrictInt = Field(ge=0)
    outputTokens: StrictInt = Field(ge=0)


class ImportedRecord(StrictModel):
    requestSha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    modelId: str = Field(min_length=1)
    modelParameters: dict
    promptVersion: str = Field(min_length=1)
    repetition: StrictInt = Field(ge=0)
    latencyMs: float = Field(ge=0)
    costUsd: float = Field(ge=0)
    usage: Usage
    output: dict


def canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def validate_config(config):
    if config['protocolVersion'] != 'llm-baseline-1.0' or (config['selectionSplit'], config['evaluationSplit']) != ('validation', 'test'):
        raise ValueError('Frozen protocol and validation-only selection required')
    if type(config['repeats']) is not int or not 1 <= config['repeats'] <= 10 or type(config['minValidRepeats']) is not int or not 1 <= config['minValidRepeats'] <= config['repeats']:
        raise ValueError('Bounded repeat count and minimum valid repeats required')
    if type(config['randomSeed']) is not int or not isinstance(config['modelId'], str) or not config['modelId'].strip():
        raise ValueError('Model identifier and integer seed required')
    def secrets(value):
        if isinstance(value, dict):
            return any(str(k).lower() in {'api_key', 'apikey', 'authorization', 'password', 'secret'} or secrets(v) for k, v in value.items())
        return isinstance(value, list) and any(secrets(v) for v in value)
    if secrets(config):
        raise ValueError('Do not store secrets in experiment configuration')
    canonical_json(config['modelParameters'])
    if not config['fixedThresholds'] or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0 <= x <= 1.000001 for x in config['fixedThresholds']):
        raise ValueError('Finite threshold grid required')
    budget = config['budget']
    if any(type(budget[k]) is not int or budget[k] < 1 for k in ('maxRequests', 'maxInputTokens', 'maxOutputTokens')) or isinstance(budget['maxCostUsd'], bool) or not isinstance(budget['maxCostUsd'], (int, float)) or not math.isfinite(budget['maxCostUsd']) or budget['maxCostUsd'] < 0:
        raise ValueError('Finite nonnegative cost and positive token/request budgets required')


def verify_permission(case):
    if case.get('synthetic') is True and case.get('source_type') == 'synthetic':
        return True
    permission = case.get('llm_authorization') or {}
    return isinstance(permission, dict) and permission.get('authorized') is True and permission.get('scope') == 'LOCAL_EXPORT_AND_IMPORT' and all(
        isinstance(permission.get(k), str) and permission[k].strip() for k in ('reference', 'reviewer_id'))


def build_request(case, config, repetition, picas_context=None):
    question = case['question']
    background = case.get('natural_reference_context') or {}
    context = {'question': {k: question.get(k, '') for k in ('title', 'description', 'input_format', 'output_format', 'constraints_text')},
        'template': {k: background.get(k, '') for k in ('template_status', 'template_code', 'template_language', 'template_source')},
        'languageA': case['language_a'], 'languageB': case['language_b'],
        **{'code' + side.upper(): [{'line': i, 'text': line} for i, line in enumerate(case['code_' + side].splitlines(), 1)] for side in ('a', 'b')}}
    if picas_context is not None:
        context['picasReviewContext'] = picas_context
    prompt = (ROOT / config['promptFile']).read_text(encoding='utf-8')
    schema = Review.model_json_schema()
    messages = [{'role': 'system', 'content': prompt + '\nJSON Schema:\n' + canonical_json(schema)},
                {'role': 'user', 'content': canonical_json(context)}]
    body = {'modelId': config['modelId'], 'modelParameters': config['modelParameters'], 'promptVersion': config['promptVersion'],
            'schemaVersion': SCHEMA_VERSION, 'repetition': repetition, 'messages': messages}
    return {'requestSha256': digest(canonical_json(body).encode()), **body}


def validate_output(value, case):
    result = Review.model_validate(value).model_dump()
    if result['outcome'] == 'ABSTAIN' and result['riskScore'] is not None or result['outcome'] != 'ABSTAIN' and result['riskScore'] is None:
        raise ValueError('ABSTAIN requires null; assessed output requires a finite score')
    if result['outcome'] == 'REVIEW_SIGNAL' and not result['evidence']:
        raise ValueError('Review signal requires source evidence')
    text = ' '.join([result['summary'], *result['limitations'], *(e['reason'] for e in result['evidence'])]).lower()
    if any(term in text for term in ('确认抄袭', '作弊成立', '证明抄袭', 'confirmed plagiarism', 'proven plagiarism', 'cheating confirmed', 'definitely plagiarized')):
        raise ValueError('Conclusive relationship statements are forbidden')
    for finding in result['evidence']:
        for side in ('a', 'b'):
            span, lines = finding['code' + side.upper()], case['code_' + side].splitlines()
            if span['startLine'] > span['endLine'] or span['endLine'] > len(lines) or not span['quote'].strip() or span['quote'] not in '\n'.join(lines[span['startLine'] - 1:span['endLine']]):
                raise ValueError('Evidence quote or inclusive line range does not match original source')
    return result


def import_records(path):
    entries = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if not isinstance(entry, dict) or not isinstance(entry.get('requestSha256'), str):
            raise ValueError('Imported JSONL needs requestSha256 records')
        key = entry['requestSha256']
        if key in entries:
            raise ValueError('Duplicate imported request identity')
        entries[key] = entry
    return entries


def cache_record(path, request):
    if not path.resolve().is_relative_to(path.parent.resolve()):
        raise ValueError('Unsafe cache path')
    if not path.exists():
        return None
    entry = json.loads(path.read_bytes())
    if not isinstance(entry, dict) or entry.get('requestSha256') != request['requestSha256'] or entry.get('recordSha256') != digest(canonical_json(entry.get('record')).encode()):
        raise ValueError('Corrupt or mismatched cache record')
    return entry['record']


def process_requests(plans, config, mode, entries=None, cache_dir=None):
    if mode not in MODES:
        raise ValueError('No network mode exists; choose mock, dry-run or import')
    entries = entries or {}
    if cache_dir and any(part in {'.git', '.aws', '.codex', '.agents'} for part in cache_dir.resolve().parts):
        raise ValueError('Unsafe cache directory')
    budget = config['budget']
    keys = {r['requestSha256'] for r, _ in plans}
    if len(keys) > budget['maxRequests']:
        raise ValueError('request budget exceeded')
    ledger = {'newNetworkCalls': 0, 'newCostUsd': 0.0, 'declaredHistoricalCostUsd': 0.0,
              'declaredInputTokens': 0, 'declaredOutputTokens': 0, 'plannedUniqueRequests': len(keys)}
    prepared, metered = [], set()
    for request, case in plans:
        key, cached = request['requestSha256'], None
        if mode == 'import' and cache_dir:
            cached = cache_record(cache_dir / (key + '.json'), request)
        entry = entries.get(key) or cached
        parsed, metadata, error = None, None, ''
        if mode == 'import' and entry:
            try:
                parsed = ImportedRecord.model_validate(entry).model_dump()
                metadata = {k: parsed[k] for k in ('latencyMs', 'costUsd', 'usage')}
                if key not in metered:
                    metered.add(key)
                    ledger['declaredHistoricalCostUsd'] += parsed['costUsd']
                    ledger['declaredInputTokens'] += parsed['usage']['inputTokens']
                    ledger['declaredOutputTokens'] += parsed['usage']['outputTokens']
                if any(parsed[k] != request[k] for k in ('requestSha256', 'modelId', 'modelParameters', 'promptVersion', 'repetition')):
                    raise ValueError('Response identity mismatch')
                parsed['output'] = validate_output(parsed['output'], case)
            except ValueError:
                error, parsed = 'SCHEMA_IDENTITY_OR_EVIDENCE_INVALID', None
        prepared.append((request, parsed, metadata, error, cached is not None))
    if ledger['declaredHistoricalCostUsd'] > budget['maxCostUsd'] + 1e-12 or ledger['declaredInputTokens'] > budget['maxInputTokens'] or ledger['declaredOutputTokens'] > budget['maxOutputTokens']:
        raise ValueError('declared historical cost/token budget exceeded; no cache written')
    rows = []
    for request, parsed, metadata, error, was_cached in prepared:
        key = request['requestSha256']
        status = 'MOCK_ONLY' if mode == 'mock' else 'DRY_RUN' if mode == 'dry-run' else 'INVALID_RECORD' if error else 'CACHE_HIT' if parsed and was_cached else 'IMPORTED' if parsed else 'IMPORT_MISSING'
        if mode == 'import' and parsed and cache_dir and not was_cached:
            cache_dir.mkdir(parents=True, exist_ok=True)
            path = cache_dir / (key + '.json')
            payload = {'requestSha256': key, 'recordSha256': digest(canonical_json(parsed).encode()), 'record': parsed}
            if path.exists():
                if cache_record(path, request) != parsed:
                    raise ValueError('Conflicting cache record')
            else:
                with path.open('x', encoding='utf-8') as handle:
                    json.dump(payload, handle, ensure_ascii=False, indent=2)
        rows.append({'requestSha256': key, 'repetition': request['repetition'], 'status': status,
            'score': parsed['output']['riskScore'] if parsed else None, 'error': error,
            'latencyMs': metadata['latencyMs'] if metadata else None, 'costUsd': metadata['costUsd'] if metadata else None,
            'inputTokens': metadata['usage']['inputTokens'] if metadata else None, 'outputTokens': metadata['usage']['outputTokens'] if metadata else None,
            'output': parsed['output'] if parsed else None})
    return rows, ledger


def aggregate(rows, config):
    scores = [r['score'] for r in rows if r['score'] is not None]
    return {'llm': statistics.mean(scores) if len(scores) >= config['minValidRepeats'] else None,
        'valid_scored_repeats': len(scores), 'llm_stddev': statistics.pstdev(scores) if len(scores) >= 2 else None,
        'llm_range': max(scores) - min(scores) if len(scores) >= 2 else None,
        'repeated_latency_ms': sum(r['latencyMs'] for r in rows if r['latencyMs'] is not None)}


def evaluate(rows, config):
    methods = [('PICAS_FIXED', 'full'), ('PICAS_RULE_DYNAMIC', 'full'), ('JPLAG', 'jplag'), ('DIRECT_LLM', 'llm')]
    selection, metrics = {}, []
    for scope in ('COMMON_THREE', 'COMMON_PICAS_JPLAG', 'AVAILABLE_DIAGNOSTIC'):
        common = [r for r in rows if r['label'] in LABELS and
            (scope == 'AVAILABLE_DIAGNOSTIC' or r.get('jplag') is not None and (scope != 'COMMON_THREE' or r.get('llm') is not None))]
        for name, field in methods:
            if scope == 'COMMON_PICAS_JPLAG' and name == 'DIRECT_LLM':
                continue
            pool = [r for r in common if r.get(field) is not None]
            point = select_operating_point([{**r, 'full': r[field]} for r in pool],
                {'name': name, 'scoreMode': 'PRODUCTION', 'thresholdMode': 'RULE' if name == 'PICAS_RULE_DYNAMIC' else 'FIXED'}, config)
            selection[scope + ':' + name] = point
            for split in ('validation', 'test'):
                samples = [r for r in pool if r['split'] == split]
                predictions = [r[field] >= (r['dynamic_threshold'] if name == 'PICAS_RULE_DYNAMIC' else point['parameter']) if point['parameter'] is not None else None for r in samples]
                metrics.append({'method': name, 'scope': scope, 'split': split, 'threshold': point['parameter'],
                    **binary_metrics(samples, predictions)})
    return {'selection': selection, 'metrics': metrics}


def load_jplag(directory, cases, dataset_version):
    import csv
    if directory is None:
        return {}, {'status': 'NOT_PROVIDED', 'matched': 0}
    metadata = json.loads((directory / 'run_manifest.json').read_bytes())
    if metadata.get('datasetVersion') != dataset_version or metadata.get('execute') is not True or metadata.get('status') not in {'FINISHED', 'PARTIAL'}:
        raise ValueError('JPlag executed manifest must match the dataset')
    known, scores, seen = {c['pair_id']: c for c in cases}, {}, set()
    with (directory / 'baseline_results.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            pair_id = row['pairId']
            if pair_id not in known or pair_id in seen:
                raise ValueError('JPlag duplicate or unknown pair')
            seen.add(pair_id)
            case = known[pair_id]
            for key, expected in [('problemId', case['problem_id']), ('datasetSplit', case['split']), ('experimentLabel', case['experiment_label']),
                                  ('language', case['language_a']), ('codeASha256', case['code_a_sha256']), ('codeBSha256', case['code_b_sha256'])]:
                if row.get(key) != expected:
                    raise ValueError('JPlag source/context identity mismatch: ' + pair_id)
            context = case.get('natural_reference_context') or {}
            if context.get('template_status') == 'REGISTERED':
                continue  # Existing raw JPlag adapter has no shared-template removal protocol.
            if row['resultStatus'] == 'MATCHED':
                scores[pair_id] = unit(float(row['predictedScore']))
    return scores, {'status': 'EXACT_SOURCE_ALIGNED_RAW_VIEW', 'matched': len(scores), 'version': metadata['toolVersion'],
        'manifestSha256': digest((directory / 'run_manifest.json').read_bytes()), 'csvSha256': digest((directory / 'baseline_results.csv').read_bytes())}


def write_jsonl(path, rows):
    with path.open('x', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')


def run(config_path, output, mode='mock', allow_development=False, responses=None, cache_dir=None, jplag_dir=None, export_prompts=False):
    if output.exists():
        raise FileExistsError('Immutable output: use a new directory')
    started, clock = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    data = config_path.read_bytes()
    config = json.loads(data)
    validate_config(config)
    if responses and mode != 'import':
        raise ValueError('Responses are only consumed in import mode')
    if mode not in MODES or mode == 'import' and ('MOCK' in config['modelId'] or 'FILL_' in config['modelId']):
        raise ValueError('Import requires an exact, non-placeholder model identifier; no network mode exists')
    manifest_path = ROOT / config['datasetManifest']
    manifest, cases, validation = load_research_dataset(manifest_path)
    groups = verify_isolation(cases)
    blockers = quality_blockers(cases, manifest, digest(data))
    registration = manifest.get('evaluation_registration') or {}
    frozen = {'prompt_sha256': digest((ROOT / config['promptFile']).read_bytes()),
              'schema_sha256': digest(canonical_json(Review.model_json_schema()).encode()),
              'dataset_sha256': digest(canonical_json(cases).encode())}
    if any(registration.get(k) != value for k, value in frozen.items()):
        blockers.append('LLM prompt/schema/dataset snapshot preregistration required')
    if not allow_development and (blockers or mode != 'import'):
        raise ValueError('Formal LLM evaluation requires reviewed frozen data and genuine imported model records')
    baseline, baseline_meta = load_jplag(jplag_dir, cases, manifest['dataset_version'])
    rows, excluded, plans, owner, approved = [], [], [], {}, []
    for index, case in enumerate(cases, 1):
        if not case['eligible_for_core_metrics'] or case['experiment_label'] not in LABELS or case['language_a'] != case['language_b'] or case['language_a'] not in {'java', 'python'}:
            excluded.append({'pair_id': case['pair_id'], 'reason': 'OUTSIDE_FROZEN_SAME_LANGUAGE_KNOWN_LABEL_SCOPE'})
            continue
        row = extract_query(case, index, groups[case['pair_id']])
        row.update(jplag=baseline.get(case['pair_id']), llm=None, model_scope='AUTHORIZED_LOCAL_ONLY' if verify_permission(case) else 'LLM_SCOPE_DENIED')
        for key in ('retrieval_query_id', 'retrieval_pool_complete', 'retrieval_pool_size', 'query_source_sha256'):
            if key in case:
                row[key] = case[key]
        row.update(code_a_sha256=case['code_a_sha256'], code_b_sha256=case['code_b_sha256'])
        rows.append(row)
        if verify_permission(case):
            approved.append(case['pair_id'])
            for repetition in range(config['repeats']):
                request = build_request(case, config, repetition)
                plans.append((request, case))
                owner[request['requestSha256']] = case['pair_id']
    entries = import_records(responses) if responses else {}
    if set(entries) - {r['requestSha256'] for r, _ in plans}:
        raise ValueError('Imported responses contain unknown request identities')
    repeats, usage = process_requests(plans, config, mode, entries, cache_dir)
    for result, (_, case) in zip(repeats, plans):
        result['pair_id'] = case['pair_id']
    for row in rows:
        row.update(aggregate([r for r in repeats if r['pair_id'] == row['pair_id']], config))
    result = evaluate(rows, config)
    failures, borderline = [], []
    for row in rows:
        if row['llm'] is None:
            failures.append({'pair_id': row['pair_id'], 'split': row['split'], 'reason': 'LLM_SCORE_UNAVAILABLE', 'score': None})
            continue
        point = result['selection']['AVAILABLE_DIAGNOSTIC:DIRECT_LLM']['parameter']
        if point is None:
            continue
        predicted = row['llm'] >= point
        if predicted != (row['label'] in POSITIVE_LABELS):
            failures.append({'pair_id': row['pair_id'], 'split': row['split'], 'reason': 'FALSE_POSITIVE' if predicted else 'FALSE_NEGATIVE', 'score': row['llm']})
        if abs(row['llm'] - point) <= .05:
            borderline.append({'pair_id': row['pair_id'], 'split': row['split'], 'score': row['llm'], 'threshold': point, 'distance': abs(row['llm'] - point)})
    output.mkdir(parents=True)
    write_json(output / 'config.json', config)
    write_json(output / 'dataset_validation.json', validation)
    write_json(output / 'selection.json', result['selection'])
    write_json(output / 'review.schema.json', Review.model_json_schema())
    write_jsonl(output / 'scores.jsonl', rows)
    write_jsonl(output / 'model_outputs.jsonl', repeats)
    write_jsonl(output / 'requests.jsonl', [{'pair_id': case['pair_id'], **{k: request[k] for k in ('requestSha256', 'repetition', 'modelId', 'modelParameters', 'promptVersion')}} for request, case in plans])
    write_jsonl(output / 'responses_template.jsonl', [{'requestSha256': request['requestSha256'], 'modelId': request['modelId'],
        'modelParameters': request['modelParameters'], 'promptVersion': request['promptVersion'], 'repetition': request['repetition'],
        'latencyMs': None, 'costUsd': None, 'usage': None, 'output': None} for request, _ in plans])
    if export_prompts:
        write_jsonl(output / 'prompts.jsonl', [r for r, _ in plans])
    for name, records in [('metrics', result['metrics']), ('excluded', excluded), ('failures', failures), ('borderline', borderline), ('repetitions', [{k: v for k, v in r.items() if k != 'output'} for r in repeats]),
        ('stability', [{k: r[k] for k in ('pair_id', 'valid_scored_repeats', 'llm', 'llm_stddev', 'llm_range', 'repeated_latency_ms')} for r in rows]),
        ('coverage', [{'method': name, 'requested': len(rows), 'available': sum(r.get(field) is not None for r in rows)} for name, field in [('PICAS', 'full'), ('JPLAG', 'jplag'), ('DIRECT_LLM', 'llm')]])]:
        write_csv(output / (name + '.csv'), records)
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, capture_output=True, text=True)
    files = sorted((ROOT / 'analysis-service-python/app').rglob('*.py')) + sorted((ROOT / 'experiment').glob('*.py')) + [ROOT / config['promptFile'], ROOT.parent / 'coderisk_docs/FORMULA_SPEC.md']
    record = {'status': 'COMPLETED_MOCK_OR_DRY_WORKFLOW_ONLY' if mode != 'import' else 'COMPLETED_IMPORTED_RESPONSES_NOT_EXTERNALLY_ATTESTED',
        'claimLevel': 'DEVELOPMENT_NOT_BENCHMARK' if allow_development else 'FROZEN_REVIEWED_IMPORTED_OBSERVATION',
        'mode': mode, 'protocolVersion': config['protocolVersion'], 'formulaVersion': FORMULA_VERSION,
        'python': platform.python_version(),
        'algorithmVersion': 'SOURCE_HASHES_RECORDED', 'modelId': config['modelId'], 'modelParameters': config['modelParameters'],
        'promptVersion': config['promptVersion'], 'schemaVersion': SCHEMA_VERSION, 'randomSeed': config['randomSeed'],
        'runId': output.name, 'gitCommit': git.stdout.strip(), 'workingTreeDirty': bool(dirty.stdout.strip()), 'datasetVersion': manifest['dataset_version'],
        'datasetSha256': digest(canonical_json(cases).encode()), 'configSha256': digest(data),
        'sourceHashes': {p.relative_to(ROOT.parent).as_posix(): digest(p.read_bytes()) for p in files},
        'responseFileSha256': digest(responses.read_bytes()) if responses else None,
        'schemaSha256': digest(canonical_json(Review.model_json_schema()).encode()),
        'formalBlockers': blockers, 'formalEligiblePairs': 0 if allow_development else len(rows),
        'inputPairs': len(cases), 'analyzedPairs': len(rows), 'excludedPairs': len(excluded), 'authorizedPairs': len(approved),
        'realModelResponses': len({r['requestSha256'] for r in repeats if r['status'] in {'IMPORTED', 'CACHE_HIT'}}),
        'scoredModelPairs': sum(r['llm'] is not None for r in rows), 'jplag': baseline_meta, **usage,
        'productionFormulaChanged': False, 'promptsExported': export_prompts, 'testUsedForSelection': False,
        'startedAtUtc': started, 'completedAtUtc': datetime.now(timezone.utc).isoformat(), 'elapsedSeconds': time.perf_counter() - clock}
    write_json(output / 'run_manifest.json', record)
    report = ['# Offline Direct LLM comparison', '', '**' + record['claimLevel'] + '**', '',
        f"Mode: {mode}. Pairs: {len(rows)}. Imported/cached records: {record['realModelResponses']}. Scored LLM pairs: {record['scoredModelPairs']}.",
        'No network adapter, paid call, source execution or production scoring change. Mock/dry-run scores are null, never model accuracy.',
        'COMMON_THREE is the matched-source main table; COMMON_PICAS_JPLAG is a separate matched baseline subset. AVAILABLE_DIAGNOSTIC has unequal coverage.',
        'Test thresholds are frozen from validation only. Missing/abstained/invalid scores are N/A, not negative examples or zero.',
        'Imported latency/token/cost are provider-declared historical metadata, not measurements of new inference by this tool; new network calls/cost are always zero.',
        'Cache checks integrity/context but cannot attest provider execution. Repeating one historical response does not establish model stability.',
        'Exact quoted line ranges are verified; located evidence does not establish derivation or semantic equivalence.', '',
        '| Method | Scope | Test N | F1 | FPR |', '| --- | --- | ---: | ---: | ---: |']
    fmt = lambda x: 'N/A' if x is None else f'{x:.4f}'
    for metric in result['metrics']:
        if metric['split'] == 'test':
            report.append(f"| {metric['method']} | {metric['scope']} | {metric['n']} | {fmt(metric['f1'])} | {fmt(metric['fpr'])} |")
    (output / 'REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/experiments/llm_baseline_v1.json')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--mode', choices=sorted(MODES), default='mock')
    parser.add_argument('--allow-development', action='store_true')
    parser.add_argument('--responses', type=Path)
    parser.add_argument('--cache-dir', type=Path)
    parser.add_argument('--jplag-dir', type=Path)
    parser.add_argument('--export-prompts', action='store_true')
    parser.add_argument('--write-schema', type=Path, help='Generate the versioned schema; refuses existing target')
    args = parser.parse_args()
    if args.write_schema:
        if args.write_schema.exists():
            raise FileExistsError('Schema already exists')
        args.write_schema.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.write_schema, Review.model_json_schema())
        return
    if args.output is None:
        parser.error('--output required unless --write-schema')
    result = run(args.config.resolve(), args.output.resolve(), args.mode, args.allow_development,
        args.responses.resolve() if args.responses else None, args.cache_dir.resolve() if args.cache_dir else None,
        args.jplag_dir.resolve() if args.jplag_dir else None, args.export_prompts)
    print(json.dumps({k: result[k] for k in ('status', 'mode', 'analyzedPairs', 'realModelResponses', 'newNetworkCalls', 'newCostUsd')}))


if __name__ == '__main__':
    main()
