"""Statistical contracts and metadata mocks, not verified independent submissions."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiment'))
from natural_similarity_calibration import (compare_policies, disjoint_pairs, empirical_tail,
    query_tail, reference_issues, run, select_alpha, validate_reference_isolation,
    digest, extract_query, load_references, registration_issues, validate_config)


def config():
    return json.loads((ROOT / 'configs/experiments/natural_calibration_v1.json').read_text())


def reference(index, score=.4):
    return {'reference_id': str(index), 'problem_id': 'p', 'language': 'python', 'context_key': 'NONE',
            'score': score, 'authors': [f'ra{index}', f'rb{index}'], 'sources': [f'sa{index}', f'sb{index}'],
            'families': [f'fa{index}', f'fb{index}'], 'hashes': [f'ha{index}', f'hb{index}']}


def query(pair='v', split='validation', label='TRANSFORMED', **changes):
    row = {'pair_id': pair, 'split': split, 'label': label, 'problem_id': 'p', 'language': 'python',
           'full': .8, 'dynamic_threshold': .68, 'canonical_available': True, 'context_key': 'NONE',
           'effective_tokens': 100, 'template_coverage': 0,
           'authors': ['qa', 'qb'], 'sources': ['qs1', 'qs2'], 'families': ['qf1', 'qf2'],
           'hashes': ['qh1', 'qh2'], 'q_smoothed': .02, 'q_available': True}
    row.update(changes)
    return row


def test_tail_is_upper_probability_with_conservative_ties_and_smoothing():
    result = empirical_tail([.1, .4, .4, .8], .4)
    assert result['tail_count'] == 3 and result['q_empirical'] == .75
    assert result['q_smoothed'] == .8 and result['resolution'] == .2
    assert empirical_tail([.1, .4], .9)['q_smoothed'] == pytest.approx(1 / 3)
    assert empirical_tail([], .9)['q_smoothed'] is None


def test_tail_is_monotone_and_small_samples_cannot_create_zero_tail():
    values = [empirical_tail([.1, .3, .7], x)['q_smoothed'] for x in [0, .1, .3, .8, 1]]
    assert values == sorted(values, reverse=True)
    assert values[-1] == .25


@pytest.mark.parametrize('scores,target', [([float('nan')], .4), ([-.1], .4), ([.2], 1.1), ([True], .4)])
def test_invalid_scores_rejected(scores, target):
    with pytest.raises(ValueError):
        empirical_tail(scores, target)


def test_disjoint_matching_is_order_stable_and_never_selects_on_score():
    refs = [reference(i) for i in range(6)]
    refs[1]['authors'][0] = refs[0]['authors'][0]
    first, dropped = disjoint_pairs(refs, 20261010)
    selected_ids = [r['reference_id'] for r in first]
    assert dropped and len(first) == 5
    for row in refs:
        row['score'] = .99
    assert selected_ids == [r['reference_id'] for r in disjoint_pairs(list(reversed(refs)), 20261010)[0]]
    seen = set()
    for row in first:
        identifiers = {(key, value) for key in ('authors', 'sources', 'families', 'hashes') for value in row[key]}
        assert not seen & identifiers
        seen |= identifiers


@pytest.mark.parametrize('changes,reason', [
    ({'canonical_available': False}, 'PARSER_OR_NORMALIZATION_FALLBACK'),
    ({'effective_tokens': 12}, 'SHORT_EFFECTIVE_CODE'),
    ({'template_coverage': .8}, 'TEMPLATE_DOMINATED'),
    ({'authors': []}, 'QUERY_IDENTITIES_UNDECLARED'),
    ({'context_key': None}, 'TEMPLATE_CONTEXT_UNDECLARED'),
])
def test_query_guards_do_not_invent_q(changes, reason):
    pools = {('p', 'python', 'NONE'): [reference(i) for i in range(20)]}
    result = query_tail(query(**changes), pools, config())
    assert result['q_smoothed'] is None and reason in result['reasons']


def test_sample_shortage_and_unseen_problem_are_explicit():
    cfg = config()
    pool = {('p', 'python', 'NONE'): [reference(0)]}
    assert 'INSUFFICIENT_DISJOINT_REFERENCE_PAIRS' in query_tail(query(), pool, cfg)['reasons']
    assert 'COLD_START_NO_MATCHED_REFERENCE' in query_tail(query(problem_id='new'), pool, cfg)['reasons']
    refs = {('p', 'python', 'NONE'): [reference(i) for i in range(20)]}
    assert query_tail(query(), refs, cfg)['q_smoothed'] == pytest.approx(1 / 21)
    assert 'PROBLEM_DISJOINT_TEST_COLD_START' in query_tail(query(split='test'), refs, cfg)['reasons']


@pytest.mark.parametrize('key', ['authors', 'sources', 'families', 'hashes'])
def test_reference_query_identity_leakage_is_fatal(key):
    ref, case = reference(0), query()
    case[key][0] = ref[key][0]
    with pytest.raises(ValueError, match='leakage'):
        validate_reference_isolation([ref], [case], 'PREREGISTERED_CONTEXT_PANEL')


def test_default_policy_rejects_reference_test_problem_overlap():
    with pytest.raises(ValueError, match='validation problems'):
        validate_reference_isolation([reference(0)], [query(split='test')], 'VALIDATION_PROBLEMS_ONLY')
    validate_reference_isolation([reference(0)], [query(split='test')], 'PREREGISTERED_CONTEXT_PANEL')


def test_same_problem_label_and_ai_review_never_establish_independence():
    # Deliberately incomplete test metadata; not a real manual record.
    record = {'reference_id': 'metadata-mock', 'source_type': 'synthetic', 'synthetic': True,
              'review': {'label': 'INDEPENDENT', 'reviewer_a_type': 'AI', 'reviewer_b_type': 'HUMAN'}}
    reasons = reference_issues(record)
    assert 'NON_REAL_OR_UNSUPPORTED_REFERENCE_SOURCE' in reasons
    assert 'INDEPENDENT_HUMAN_RELATION_REVIEW_REQUIRED' in reasons


def test_identity_whitespace_cannot_hide_dependency_or_leakage():
    refs = [reference(0), reference(1)]
    refs[1]['authors'][0] = '  ' + refs[0]['authors'][0] + ' '
    assert len(disjoint_pairs(refs, 1)[0]) == 1
    case = query(authors=[refs[0]['authors'][0] + ' ', 'other'])
    with pytest.raises(ValueError, match='leakage'):
        validate_reference_isolation([refs[0]], [case], 'PREREGISTERED_CONTEXT_PANEL')


def test_test_labels_and_q_values_cannot_select_alpha():
    samples = [query(), query(pair='vn', label='INDEPENDENT', full=.3, q_smoothed=.8),
               query(pair='t', split='test', q_smoothed=.9)]
    first = select_alpha(samples, config())
    samples[-1].update(label='INDEPENDENT', full=.99, q_smoothed=.001)
    assert first == select_alpha(samples, config())
    assert first['selection_split'] == 'validation' and first['alpha'] is not None


def test_no_reference_support_is_rule_fallback_not_statistical_success():
    samples = [query(q_available=False, q_smoothed=None),
               query(pair='vn', label='INDEPENDENT', full=.3, q_available=False, q_smoothed=None),
               query(pair='t', split='test', q_available=False, q_smoothed=None)]
    result = compare_policies(samples, config())
    assert result['alpha_selection']['alpha'] is None
    prediction = result['predictions'][-1]
    assert prediction['statistical_predicted'] == prediction['rule_predicted']
    assert prediction['decision_source'] == 'RULE_FALLBACK'
    assert all(r['n'] == 0 for r in result['metrics'] if r['scope'] == 'CALIBRATABLE_ONLY')


def test_seed_run_has_zero_trusted_references_and_is_immutable(tmp_path):
    output = tmp_path / 'run'
    cfg = ROOT / 'configs/experiments/natural_calibration_v1.json'
    with pytest.raises(ValueError, match='Formal run blocked'):
        run(cfg, output)
    assert not output.exists()
    result = run(cfg, output, True)
    assert result['trustedReferencePairs'] == result['calibratableQueries'] == result['formalEligiblePairs'] == 0
    assert result['status'] == 'COMPLETED_DEVELOPMENT_NO_STATISTICAL_EFFECT_CLAIM'
    for filename in ('run_manifest.json', 'queries.csv', 'reference_audit.csv', 'metrics.csv', 'predictions.csv',
                     'results.json', 'selection.json', 'REPORT.md', 'mathematical_contracts.json'):
        assert (output / filename).exists()
    with pytest.raises(FileExistsError):
        run(cfg, output, True)


CODE = ('def solve(values):\n    total = 0\n    count = 0\n    for value in values:\n'
        '        if value > 0:\n            total = total + value * 2\n            count = count + 1\n'
        '        else:\n            total = total - value\n    return total + count\nprint(solve([1, 2, 3]))\n')


def mock_reference_manifest(tmp_path):
    """Test-only declarations. These are NOT externally verified HUMAN/source records."""
    for side in ('a', 'b'):
        (tmp_path / (side + '.py')).write_bytes(CODE.encode())
    record = {**reference(0), 'active': True, 'source_type': 'manual', 'synthetic': False,
        'code_a_path': 'a.py', 'code_b_path': 'b.py', 'code_a_sha256': digest(CODE.encode()), 'code_b_sha256': digest(CODE.encode()),
        'template_status': 'NONE', 'question': {'title': 'Test-only fixture', 'description': 'Not verified human data.'},
        'provenance': {'license_or_authorization': 'MOCK_TEST_ONLY', 'source_reference': 'MOCK_TEST_ONLY'},
        'review': {'status': 'AGREED', 'label': 'INDEPENDENT', 'reviewer_a': 'MOCK_A', 'reviewer_b': 'MOCK_B',
            'reviewer_a_type': 'HUMAN', 'reviewer_b_type': 'HUMAN', 'independence_confirmed': True, 'relation_verified': True,
            'label_basis': 'MOCK_TEST_ONLY', 'reviewed_at': '2026-10-10', 'functional_evidence': 'MOCK_TEST_ONLY'}}
    record.pop('hashes')
    manifest = {'schema_version': 'independent-reference-1.0', 'dataset_version': 'MOCK_TEST_ONLY', 'records': [record],
        'registration': {'status': 'FROZEN', 'registered_at': '2026-10-10T00:00:00+00:00',
            'frozen_before_test_access': True, 'evidence_reference': 'MOCK_TEST_ONLY'}}
    return manifest


def save_manifest(tmp_path, manifest):
    manifest['registration']['records_sha256'] = digest(json.dumps(manifest['records'], sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode())
    path = tmp_path / 'refs.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    return path


def test_reference_loader_uses_actual_local_source_and_duplicate_matching(tmp_path):
    manifest = mock_reference_manifest(tmp_path)
    path = save_manifest(tmp_path, manifest)
    _, refs, pools, audit, blockers = load_references(path, config())
    assert not blockers and audit[0]['trusted']
    assert refs[0]['hashes'] == ['sha256:' + digest(CODE.encode())] * 2
    assert refs[0]['score'] == 1 and len(pools[('p', 'python', 'NONE')]) == 1
    # Equal content within one mock-reviewed pair is allowed; reuse across pairs is not.
    other = copy.deepcopy(manifest['records'][0])
    other.update(reference_id='different', authors=['other-a', 'other-b'], sources=['other-1', 'other-2'], families=['other-f1', 'other-f2'])
    manifest['records'].append(other)
    _, _, pools, audit, _ = load_references(save_manifest(tmp_path, manifest), config())
    assert len(pools[('p', 'python', 'NONE')]) == 1
    assert sum(r['trusted'] for r in audit) == 1
    assert any('REUSED_AUTHOR_SOURCE_FAMILY_OR_HASH' in r['reasons'] for r in audit)
    manifest['records'][0]['review']['reviewer_b'] = ' MOCK_A '
    assert 'INDEPENDENT_HUMAN_RELATION_REVIEW_REQUIRED' in reference_issues(manifest['records'][0])


def test_reference_query_hash_namespace_and_windows_newlines_match(tmp_path):
    manifest = mock_reference_manifest(tmp_path)
    raw = CODE.replace('\n', '\r\n').encode()
    (tmp_path / 'a.py').write_bytes(raw)
    manifest['records'][0]['code_a_sha256'] = digest(raw)
    _, refs, _, _, _ = load_references(save_manifest(tmp_path, manifest), config())
    same_source = query(hashes=['sha256:' + digest(CODE.encode()), 'another-hash'])
    with pytest.raises(ValueError, match='leakage'):
        validate_reference_isolation(refs, [same_source], 'PREREGISTERED_CONTEXT_PANEL')


@pytest.mark.parametrize('mutation,reason', [
    ({'code_a_sha256': 'tampered'}, 'REFERENCE_HASH_MISMATCH'),
    ({'code_a_path': '../outside.py'}, 'REFERENCE_PATH_MISSING_OR_OUTSIDE_MANIFEST_ROOT'),
    ({'code_a_path': 'missing.py'}, 'REFERENCE_PATH_MISSING_OR_OUTSIDE_MANIFEST_ROOT'),
    ({'source_type': 'ai_assisted'}, 'NON_REAL_OR_UNSUPPORTED_REFERENCE_SOURCE'),
    ({'active': False}, 'INACTIVE_REFERENCE'),
])
def test_reference_quality_gate_is_not_a_development_override(tmp_path, mutation, reason):
    manifest = mock_reference_manifest(tmp_path)
    manifest['records'][0].update(mutation)
    _, _, pools, audit, _ = load_references(save_manifest(tmp_path, manifest), config())
    assert not pools and reason in audit[0]['reasons']


def test_reference_registration_cannot_hide_changed_records_or_undated_freeze(tmp_path):
    manifest = mock_reference_manifest(tmp_path)
    save_manifest(tmp_path, manifest)
    assert not registration_issues(manifest)
    manifest['records'][0]['notes'] = 'changed after freeze'
    assert registration_issues(manifest)
    save_manifest(tmp_path, manifest)
    manifest['registration']['registered_at'] = '2026-10-10T00:00:00'
    assert registration_issues(manifest)
    manifest['registration'] = ['not-an-object']
    assert registration_issues(manifest)


def test_registered_template_changes_only_guard_context_not_score():
    case = {'pair_id': 'fixture', 'problem_id': 'p', 'split': 'validation', 'experiment_label': 'UNCERTAIN',
        'language_a': 'python', 'language_b': 'python', 'code_a': CODE, 'code_b': CODE,
        'code_a_sha256': digest(CODE.encode()), 'code_b_sha256': digest(CODE.encode()), 'source_type': 'synthetic', 'synthetic': True,
        'case_type': 'MOCK', 'problem_type': 'fixture', 'question': {'title': 'Fixture', 'description': 'Test only'},
        'natural_reference_context': {'template_status': 'NONE'}}
    plain = extract_query(case, 1, 'fixture')
    case['natural_reference_context'].update(template_status='REGISTERED', template_language='python', template_code=CODE, template_source='MOCK_TEST_ONLY')
    registered = extract_query(case, 1, 'fixture')
    assert plain['full'] == registered['full'] and plain['dynamic_threshold'] == registered['dynamic_threshold']
    assert plain['effective_tokens'] >= 41 and registered['effective_tokens'] == 0
    assert registered['template_coverage'] == 1
    assert registered['context_key'] != plain['context_key']


def test_parser_failure_does_not_emit_fabricated_structural_scores():
    invalid = 'def broken(:\n    return 1\n'
    case = {'pair_id': 'fixture', 'problem_id': 'p', 'split': 'validation', 'experiment_label': 'UNCERTAIN',
        'language_a': 'python', 'language_b': 'python', 'code_a': invalid, 'code_b': CODE,
        'code_a_sha256': digest(invalid.encode()), 'code_b_sha256': digest(CODE.encode()), 'source_type': 'synthetic', 'synthetic': True,
        'case_type': 'MOCK', 'problem_type': 'fixture', 'question': {'title': 'Fixture', 'description': 'Test only'}}
    row = extract_query(case, 1, 'fixture')
    assert row['warnings'] and not row['canonical_available']
    assert row['ast'] is row['canonical'] is row['mapping'] is None
    assert row['full'] == row['raw']


@pytest.mark.parametrize('mutation', [{'selectionSplit': 'test'}, {'minIndependentPairs': 0},
    {'alphaCandidates': [float('nan')]}, {'fixedThresholds': [float('inf')]}, {'randomSeed': True}])
def test_bad_or_test_tuning_config_rejected(mutation):
    cfg = config()
    cfg.update(mutation)
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_additional_identity_declarations_cannot_cross_validation_and_test():
    samples = [query(), query(pair='t', split='test', problem_id='new')]
    with pytest.raises(ValueError, match='query.*leakage'):
        validate_reference_isolation([], samples, 'PREREGISTERED_CONTEXT_PANEL')


def test_reference_panels_cannot_reuse_authors_between_validation_and_test():
    refs = [reference(0), reference(1)]
    refs[1]['problem_id'] = 'new'
    refs[1]['authors'][0] = refs[0]['authors'][0]
    test = query(pair='t', split='test', problem_id='new', authors=['ta', 'tb'], sources=['ts1', 'ts2'], families=['tf1', 'tf2'], hashes=['th1', 'th2'])
    with pytest.raises(ValueError, match='panel.*leakage'):
        validate_reference_isolation(refs, [query(), test], 'PREREGISTERED_CONTEXT_PANEL')
