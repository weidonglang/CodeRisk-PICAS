"""Test-only candidate pools and imported responses, not benchmark labels."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiment'))
from hybrid_review import (audit_pools, select_candidates, candidate_recall, choose_k,
    verify_baseline, evaluate_pipeline, make_request, run, validate_hybrid_config)
from llm_baseline import build_request


def config():
    return json.loads((ROOT / 'configs/experiments/hybrid_review_v1.json').read_bytes())


def pool(split='validation', query='q'):
    return [{'pair_id': query + str(i), 'problem_id': split + '-p', 'split': split,
        'label': 'TRANSFORMED' if i == 2 else 'INDEPENDENT', 'full': score,
        'dynamic_threshold': .7, 'retrieval_query_id': query, 'retrieval_pool_complete': True,
        'retrieval_pool_size': 3, 'query_source_sha256': query + '-anchor',
        'code_a_sha256': query + '-anchor', 'code_b_sha256': query + '-target' + str(i),
        'question_context_sha256': 'TEST_ONLY_CONTEXT', 'language': 'python',
        'canonical': None if i == 2 else .5} for i, score in enumerate([.9, .8, .1])]


@pytest.mark.parametrize('mutation', [
    {'retrieval_pool_complete': False}, {'retrieval_pool_size': 2}, {'label': 'UNCERTAIN'},
    {'query_source_sha256': 'wrong'}, {'full': None}, {'full': float('nan')},
    {'split': 'test'}, {'question_context_sha256': 'other'}, {'dynamic_threshold': .8},
    {'code_b_sha256': 'q-target0'}, {'pair_id': 'q0'}, {'language': 'java'}])
def test_bad_or_incomplete_pools_block_without_discarding_candidates(mutation):
    rows = pool()
    rows[-1].update(mutation)
    assert audit_pools(rows)['valid'] is False


def test_fallback_candidate_is_retained_and_missed_positive_is_measured():
    rows = pool()
    assert audit_pools(rows)['valid']
    assert candidate_recall(rows, 1)['value'] == 0
    assert candidate_recall(rows, 3)['value'] == 1
    assert {r['pair_id'] for r in select_candidates(rows, 3)} == {'q0', 'q1', 'q2'}


def test_k_selected_only_on_validation_and_minimum_queries_enforced():
    cfg = config()
    cfg['minimumValidationPositiveQueries'] = 1
    rows = pool() + pool('test', 'test-q')
    first = choose_k(rows, cfg)
    assert first['k'] == 3
    rows[-1]['label'] = 'INDEPENDENT'
    rows[-1]['full'] = 1
    assert choose_k(rows, cfg) == first
    cfg['minimumValidationPositiveQueries'] = 2
    assert choose_k(rows, cfg)['k'] is None


def test_ties_are_reproducible_and_query_side_can_be_b():
    rows = pool()
    for row in rows:
        row['full'] = .5
        row['code_a_sha256'], row['code_b_sha256'] = row['code_b_sha256'], row['code_a_sha256']
    assert audit_pools(rows)['valid']
    assert [r['pair_id'] for r in select_candidates(list(reversed(rows)), 2)] == ['q0', 'q1']


def test_missing_real_baseline_never_bypassed_by_development_flag(tmp_path):
    cfg = config()
    result = verify_baseline(None, None, 'TEST_DATA', cfg)
    assert result['ready'] is False
    (tmp_path / 'run_manifest.json').write_text(json.dumps({'mode': 'mock', 'datasetSha256': 'TEST_DATA'}))
    assert verify_baseline(tmp_path, None, 'TEST_DATA', cfg)['ready'] is False


def test_baseline_requires_source_identity_hash_bound_human_review_and_matched_coverage(tmp_path):
    import csv
    from llm_baseline import digest
    cfg = config()
    cfg['llm']['modelId'] = 'TEST_ONLY_NOT_REAL_MODEL'
    files = sorted((ROOT / 'analysis-service-python/app').rglob('*.py')) + [ROOT.parent / 'coderisk_docs/FORMULA_SPEC.md']
    record = {'mode': 'import', 'claimLevel': 'FROZEN_REVIEWED_IMPORTED_OBSERVATION',
        'formalBlockers': [], 'formalEligiblePairs': 60, 'realModelResponses': 60,
        'testUsedForSelection': False, 'datasetSha256': 'TEST_DATA',
        'modelId': cfg['llm']['modelId'], 'modelParameters': cfg['llm']['modelParameters'],
        'sourceHashes': {p.relative_to(ROOT.parent).as_posix(): digest(p.read_bytes()) for p in files}}
    path = tmp_path / 'run_manifest.json'
    path.write_text(json.dumps(record))
    approval = {'status': 'APPROVED', 'reviewer_type': 'HUMAN', 'reviewer_id': 'MOCK_TEST_ONLY',
        'reference': 'MOCK_TEST_ONLY', 'recommended_for_hybrid': True,
        'reviewed_run_manifest_sha256': digest(path.read_bytes())}
    review_path = tmp_path / 'review.json'
    review_path.write_text(json.dumps(approval))
    with (tmp_path / 'metrics.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['method', 'scope', 'split', 'n'])
        writer.writeheader()
        writer.writerows({'method': method, 'scope': 'COMMON_THREE', 'split': 'test', 'n': 30}
            for method in ['PICAS_FIXED', 'PICAS_RULE_DYNAMIC', 'JPLAG', 'DIRECT_LLM'])
    assert verify_baseline(tmp_path, review_path, 'TEST_DATA', cfg)['ready']
    assert not verify_baseline(tmp_path, review_path, 'WRONG_DATA', cfg)['ready']
    approval['reviewer_type'] = 'AI'
    review_path.write_text(json.dumps(approval))
    assert not verify_baseline(tmp_path, review_path, 'TEST_DATA', cfg)['ready']


def test_unknown_selected_pair_or_malformed_pool_cannot_silently_change_denominator():
    cfg = config()
    with pytest.raises(ValueError):
        evaluate_pipeline(pool(), {'not-a-candidate'}, cfg)
    rows = pool()
    rows[-1]['label'] = 'UNCERTAIN'
    with pytest.raises(ValueError):
        evaluate_pipeline(rows, {'q0'}, cfg)


def test_actual_seed_import_cannot_bypass_real_baseline_with_development_flag(tmp_path):
    path = ROOT / 'configs/experiments/hybrid_review_v1.json'
    manifest = run(path, tmp_path / 'blocked-import', mode='import', allow_development=True)
    assert manifest['baselineGate']['ready'] is False
    assert manifest['selectedPairs'] == manifest['realModelResponses'] == 0


def test_pipeline_counts_candidate_misses_and_no_review_is_not_a_relation_proof():
    cfg = config()
    rows = pool() + pool('test', 't')
    selected = {r['pair_id'] for r in select_candidates(rows, 1)}
    for row in rows:
        row['llm'] = .9 if row['pair_id'] in selected else None
    # Selected validation examples contain one class only: no threshold learning.
    assert evaluate_pipeline(rows, selected, cfg)['status'] == 'NO_VALIDATION_OPERATING_POINT'
    rows[0]['label'] = 'TRANSFORMED'
    rows[1]['llm'] = .1
    rows[4]['llm'] = .1
    selected |= {'q1', 't1'}
    result = evaluate_pipeline(rows, selected, cfg)
    test = next(m for m in result['metrics'] if m['split'] == 'test')
    assert test['n'] == 3 and test['fn'] == 1  # Low-ranked positive stays in denominator.
    assert result['semantics'] == 'REVIEW_QUEUE_FLAG_NOT_RELATION_JUDGMENT'
    rows[4]['llm'] = None
    assert evaluate_pipeline(rows, selected, cfg)['status'] == 'SELECTED_REVIEWS_INCOMPLETE'


def test_hybrid_prompt_separate_from_direct_and_labels_never_leak():
    cfg = config()
    c = {'code_a': 'a = 1\nprint(a)', 'code_b': 'b = 1\nprint(b)',
        'question': {'title': 'Print', 'description': 'Print one value.'},
        'language_a': 'python', 'language_b': 'python', 'experiment_label': 'TRANSFORMED'}
    row = pool()[0]
    hybrid = make_request(c, row, cfg['llm'], 0)
    direct_cfg = json.loads((ROOT / 'configs/experiments/llm_baseline_v1.json').read_bytes())
    direct = build_request(c, direct_cfg, 0)
    assert hybrid['requestSha256'] != direct['requestSha256']
    prompt = json.loads(hybrid['messages'][1]['content'])
    assert prompt['picasReviewContext']['weightedSimilarityScore'] == .9
    assert 'label' not in prompt['picasReviewContext'] and 'TRANSFORMED' not in json.dumps(prompt)


@pytest.mark.parametrize('mutation', [{'candidateKs': [True]}, {'targetCandidateRecall': 2},
    {'minimumValidationPositiveQueries': 0}, {'selectionSplit': 'test'}])
def test_bad_hybrid_config_rejected(mutation):
    cfg = config()
    cfg.update(mutation)
    with pytest.raises(ValueError):
        validate_hybrid_config(cfg)


def test_actual_seed_generates_blocked_audit_no_requests_or_fake_recall(tmp_path):
    path = ROOT / 'configs/experiments/hybrid_review_v1.json'
    with pytest.raises(ValueError, match='Formal'):
        run(path, tmp_path / 'formal')
    output = tmp_path / 'mock'
    manifest = run(path, output, allow_development=True)
    assert manifest['status'] == 'BLOCKED_INCOMPLETE_QUERY_POOLS'
    assert manifest['selectedPairs'] == manifest['realModelResponses'] == manifest['newNetworkCalls'] == 0
    assert manifest['selectedK'] is None
    assert (output / 'human_review_queue.csv').exists()
    assert (output / 'requests.jsonl').read_text() == ''
    with pytest.raises(FileExistsError):
        run(path, output, allow_development=True)


def test_complete_test_only_pool_exercises_mock_queue_but_real_import_stays_gated(tmp_path, monkeypatch):
    import hybrid_review
    from llm_baseline import digest
    cfg = config()
    cfg['minimumValidationPositiveQueries'] = 1
    path = tmp_path / 'TEST_ONLY_config.json'
    path.write_text(json.dumps(cfg))
    cases, scores = [], {}
    for split, query, value in [('validation', 'v', 1), ('test', 't', 10)]:
        for row in pool(split, query):
            i = int(row['pair_id'][-1])
            a, b = f'print({value})', f'print({value + i + 2})'
            row.update(code_a_sha256=digest(a.encode()), code_b_sha256=digest(b.encode()), query_source_sha256=digest(a.encode()))
            cases.append({'pair_id': row['pair_id'], 'problem_id': row['problem_id'], 'split': split,
                'source_id': query, 'experiment_label': row['label'], 'case_type': 'TEST_ONLY',
                'language_a': 'python', 'language_b': 'python', 'code_a': a, 'code_b': b,
                'code_a_sha256': row['code_a_sha256'], 'code_b_sha256': row['code_b_sha256'],
                'synthetic': True, 'source_type': 'synthetic', 'eligible_for_core_metrics': True,
                'question': {'title': row['problem_id']}, **{k: row[k] for k in ('retrieval_query_id', 'retrieval_pool_complete', 'retrieval_pool_size', 'query_source_sha256')}})
            scores[row['pair_id']] = row
    monkeypatch.setattr(hybrid_review, 'load_research_dataset', lambda p: ({'dataset_version': 'MOCK_TEST_ONLY'}, cases, {'valid': True}))
    monkeypatch.setattr(hybrid_review, 'extract_query', lambda c, i, g: copy.deepcopy(scores[c['pair_id']]))
    mock = run(path, tmp_path / 'mock-complete', allow_development=True)
    assert mock['status'] == 'DEVELOPMENT_CANDIDATE_WORKFLOW_ONLY'
    assert mock['selectedK'] == 3 and mock['selectedPairs'] == 6 and mock['plannedUniqueRequests'] == 18
    assert mock['realModelResponses'] == mock['newNetworkCalls'] == 0
    blocked = run(path, tmp_path / 'import-complete', mode='import', allow_development=True)
    assert blocked['status'] == 'BLOCKED_REAL_BASELINE_REQUIRED' and blocked['selectedPairs'] == 0
