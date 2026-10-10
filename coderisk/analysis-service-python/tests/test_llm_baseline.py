"""Offline model-record mocks, never genuine LLM or HUMAN benchmark outputs."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiment'))
from llm_baseline import (build_request, digest, evaluate, import_records, process_requests,
    run, validate_config, validate_output, verify_permission, aggregate, load_jplag)


def config():
    return json.loads((ROOT / 'configs/experiments/llm_baseline_v1.json').read_bytes())


def case():
    return {'pair_id': 'SECRET_TRANSFORMED_TEST', 'experiment_label': 'TRANSFORMED', 'split': 'test',
        'case_type': 'VARIABLE_RENAME', 'problem_id': 'p', 'language_a': 'python', 'language_b': 'python',
        'code_a': 'value = 1\nprint(value)\n', 'code_b': 'item = 1\nprint(item)\n',
        'question': {'title': 'Print a value', 'description': 'Print the value.'},
        'source_type': 'synthetic', 'synthetic': True}


def output():
    return {'schemaVersion': 'llm-risk-review-1.0', 'outcome': 'REVIEW_SIGNAL', 'riskScore': .8,
        'summary': 'Similar assignments; human review only.', 'limitations': ['No relation proof.'],
        'evidence': [{'codeA': {'startLine': 1, 'endLine': 1, 'quote': 'value = 1'},
                      'codeB': {'startLine': 1, 'endLine': 1, 'quote': 'item = 1'}, 'reason': 'Assignment pattern.'}]}


def record(request):
    return {'requestSha256': request['requestSha256'], 'modelId': request['modelId'],
        'modelParameters': request['modelParameters'], 'promptVersion': request['promptVersion'],
        'repetition': request['repetition'], 'latencyMs': 12.0, 'costUsd': 0.0,
        'usage': {'inputTokens': 30, 'outputTokens': 20}, 'output': output()}


def test_prompt_contains_same_background_not_labels_split_or_picas_score():
    c, cfg = case(), config()
    request = build_request(c, cfg, 0)
    serialized = json.dumps(request['messages'])
    assert 'SECRET_TRANSFORMED_TEST' not in serialized and 'VARIABLE_RENAME' not in serialized
    assert 'TRANSFORMED' not in serialized and 'PICAS' not in serialized
    assert 'Print the value.' in serialized and 'value = 1' in serialized
    assert request['requestSha256'] != build_request(c, cfg, 1)['requestSha256']
    c.update(split='validation', experiment_label='INDEPENDENT', pair_id='another')
    assert request['requestSha256'] == build_request(c, cfg, 0)['requestSha256']


def test_request_cache_identity_includes_model_parameters_prompt_and_code():
    c, cfg = case(), config()
    original = build_request(c, cfg, 0)['requestSha256']
    for key, value in [('modelId', 'another'), ('promptVersion', 'another'), ('modelParameters', {'temperature': .1})]:
        assert build_request(c, {**cfg, key: value}, 0)['requestSha256'] != original
    c['code_a'] += '# changed\n'
    assert build_request(c, cfg, 0)['requestSha256'] != original


@pytest.mark.parametrize('mutation', [
    {'riskScore': True}, {'riskScore': 1.1}, {'riskScore': float('nan')}, {'outcome': 'PLAGIARISM'},
    {'unexpected': 'field'}, {'summary': '确认抄袭'}, {'evidence': []}, {'riskScore': None},
])
def test_invalid_or_conclusive_response_rejected(mutation):
    value = output()
    value.update(mutation)
    with pytest.raises(ValueError):
        validate_output(value, case())


def test_evidence_must_quote_the_actual_inclusive_range():
    value = output()
    assert validate_output(value, case())['riskScore'] == .8
    value['evidence'][0]['codeA']['startLine'] = 2
    value['evidence'][0]['codeA']['endLine'] = 2
    with pytest.raises(ValueError):
        validate_output(value, case())
    value['evidence'][0]['codeA'].update(startLine=1, endLine=99)
    with pytest.raises(ValueError):
        validate_output(value, case())


def test_real_code_permission_is_not_inferred_from_label_or_public_source():
    c = case()
    c.update(source_type='external', synthetic=False)
    assert not verify_permission(c)
    c['llm_authorization'] = {'scope': 'LOCAL_EXPORT_AND_IMPORT', 'authorized': True, 'reference': 'MOCK_ONLY', 'reviewer_id': 'MOCK_REVIEWER'}
    assert verify_permission(c)
    c['llm_authorization']['authorized'] = False
    assert not verify_permission(c)


def test_mock_and_dry_run_never_fabricate_scores_or_model_usage():
    cfg, c = config(), case()
    requests = [build_request(c, cfg, i) for i in range(3)]
    for mode in ('mock', 'dry-run'):
        rows, usage = process_requests([(r, c) for r in requests], cfg, mode)
        assert all(r['score'] is None for r in rows)
        assert usage['newNetworkCalls'] == usage['newCostUsd'] == 0
        assert usage['declaredHistoricalCostUsd'] == 0


def test_cache_is_context_bound_validated_and_cannot_be_tampered(tmp_path):
    cfg, c = config(), case()
    cfg['modelId'] = 'LOCAL_TEST_MODEL_RECORD_NOT_REAL_EVALUATION'
    req = build_request(c, cfg, 0)
    entries = {req['requestSha256']: record(req)}
    rows, _ = process_requests([(req, c)], cfg, 'import', entries, tmp_path)
    assert rows[0]['status'] == 'IMPORTED' and rows[0]['score'] == .8
    cached, _ = process_requests([(req, c)], cfg, 'import', {}, tmp_path)
    assert cached[0]['status'] == 'CACHE_HIT'
    file = next(tmp_path.glob('*.json'))
    damaged = json.loads(file.read_bytes())
    damaged['record']['output']['riskScore'] = .1
    file.write_text(json.dumps(damaged), encoding='utf-8')
    with pytest.raises(ValueError, match='cache'):
        process_requests([(req, c)], cfg, 'import', {}, tmp_path)


def test_budget_includes_imported_prior_cost_and_usage_even_for_cache(tmp_path):
    cfg, c = config(), case()
    req = build_request(c, cfg, 0)
    entry = record(req)
    entry['costUsd'] = .01
    with pytest.raises(ValueError, match='budget'):
        process_requests([(req, c)], cfg, 'import', {req['requestSha256']: entry}, tmp_path)
    assert not list(tmp_path.glob('*.json'))
    cfg['budget']['maxRequests'] = 0
    with pytest.raises(ValueError, match='budget'):
        process_requests([(req, c)], cfg, 'mock')


def test_invalid_output_still_consumes_declared_budget():
    cfg, c = config(), case()
    req = build_request(c, cfg, 0)
    entry = record(req)
    entry.update(costUsd=.01, output={'broken': 'not schema compliant'})
    with pytest.raises(ValueError, match='budget'):
        process_requests([(req, c)], cfg, 'import', {req['requestSha256']: entry})


def test_duplicate_contexts_can_share_cache_without_inflating_original_cost(tmp_path):
    cfg, c = config(), case()
    req = build_request(c, cfg, 0)
    rows, usage = process_requests([(req, c), (req, c)], cfg, 'import', {req['requestSha256']: record(req)}, tmp_path)
    assert len(rows) == 2 and len(list(tmp_path.glob('*.json'))) == 1
    assert usage['declaredInputTokens'] == 30 and usage['declaredOutputTokens'] == 20


def test_abstentions_do_not_count_as_valid_repeat_scores():
    cfg = config()
    assert aggregate([{'score': None, 'latencyMs': 10}, {'score': .8, 'latencyMs': 10}], cfg)['llm'] is None
    result = aggregate([{'score': .8, 'latencyMs': 10}, {'score': .2, 'latencyMs': 10}], cfg)
    assert result['llm'] == .5 and result['llm_range'] == pytest.approx(.6)


def test_jplag_alignment_rejects_current_source_mismatch(tmp_path):
    import csv
    c = case()
    c.update(code_a_sha256='sha256:a', code_b_sha256='sha256:b')
    (tmp_path / 'run_manifest.json').write_text(json.dumps({'datasetVersion': 'TEST_ONLY', 'execute': True, 'status': 'FINISHED', 'toolVersion': 'MOCK_VERSION'}))
    row = {'pairId': c['pair_id'], 'problemId': c['problem_id'], 'datasetSplit': c['split'], 'experimentLabel': c['experiment_label'],
        'language': 'python', 'codeASha256': 'sha256:a', 'codeBSha256': 'sha256:WRONG', 'resultStatus': 'MATCHED', 'predictedScore': .8}
    with (tmp_path / 'baseline_results.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(ValueError, match='identity mismatch'):
        load_jplag(tmp_path, [c], 'TEST_ONLY')


def test_duplicate_import_requests_rejected(tmp_path):
    req = build_request(case(), config(), 0)
    path = tmp_path / 'responses.jsonl'
    data = json.dumps(record(req))
    path.write_text(data + '\n' + data + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match='Duplicate'):
        import_records(path)


def test_test_labels_cannot_select_thresholds_and_mock_metrics_are_na():
    cfg = config()
    rows = [{'pair_id': 'v+', 'split': 'validation', 'label': 'TRANSFORMED', 'full': .9, 'dynamic_threshold': .7, 'llm': .8, 'jplag': .8},
            {'pair_id': 'v-', 'split': 'validation', 'label': 'INDEPENDENT', 'full': .2, 'dynamic_threshold': .7, 'llm': .2, 'jplag': .1},
            {'pair_id': 't', 'split': 'test', 'label': 'TRANSFORMED', 'full': .7, 'dynamic_threshold': .7, 'llm': .7, 'jplag': .6}]
    first = evaluate(rows, cfg)
    rows[-1]['label'] = 'INDEPENDENT'
    assert first['selection'] == evaluate(rows, cfg)['selection']
    for r in rows:
        r['llm'] = None
    assert all(m['n'] == 0 for m in evaluate(rows, cfg)['metrics'] if m['method'] == 'DIRECT_LLM')


@pytest.mark.parametrize('mutation', [{'selectionSplit': 'test'}, {'repeats': True}, {'minValidRepeats': 4},
    {'budget': {'maxRequests': 1, 'maxInputTokens': 1, 'maxOutputTokens': 1, 'maxCostUsd': float('inf')}},
    {'modelParameters': {'api_key': 'never-store-secrets'}}])
def test_invalid_or_secret_config_rejected(mutation):
    cfg = config()
    cfg.update(mutation)
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_seed_mock_run_is_not_real_llm_evaluation_and_is_immutable(tmp_path):
    path = ROOT / 'configs/experiments/llm_baseline_v1.json'
    with pytest.raises(ValueError, match='Formal'):
        run(path, tmp_path / 'formal')
    output_dir = tmp_path / 'mock'
    manifest = run(path, output_dir, allow_development=True)
    assert manifest['realModelResponses'] == manifest['formalEligiblePairs'] == 0
    assert manifest['newNetworkCalls'] == manifest['newCostUsd'] == 0
    for file in ('scores.jsonl', 'requests.jsonl', 'responses_template.jsonl', 'metrics.csv', 'repetitions.csv',
                 'stability.csv', 'REPORT.md', 'run_manifest.json', 'coverage.csv', 'failures.csv', 'borderline.csv'):
        assert (output_dir / file).exists()
    assert not (output_dir / 'prompts.jsonl').exists()
    with pytest.raises(FileExistsError):
        run(path, output_dir, allow_development=True)
