import copy
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from check_formal_readiness import assess, case_readiness


def reviewed_case(index=0, split='validation', label='INDEPENDENT'):
    return {'pair_id': str(index), 'problem_id': str(index), 'source_id': str(index), 'split': split,
            'source_type': 'manual', 'synthetic': False, 'eligible_for_core_metrics': True,
            'split_preregistered': True, 'experiment_label': label, 'case_type': 'INDEPENDENT_SOLUTION',
            'source_family_ids': [f'a{index}', f'b{index}'], 'code_a_sha256': f'a{index}', 'code_b_sha256': f'b{index}',
            'provenance': {'license_or_authorization': 'TEST_ONLY_DECLARED_AUTHORIZATION_NOT_REAL',
                           'functional_check_status': 'PASSED', 'manual_check_status': 'VERIFIED', 'template_status': 'NONE'},
            'annotation': {'reviewer_a': 'TEST_ONLY_A', 'reviewer_b': 'TEST_ONLY_B', 'reviewer_a_type': 'HUMAN',
                'reviewer_b_type': 'HUMAN', 'independence_confirmed': True, 'status': 'AGREED', 'label': label,
                'label_basis': 'UNIT_TEST_ONLY', 'reviewed_at': '2026-10-11', 'functional_evidence': 'UNIT_TEST_ONLY',
                'independence_evidence': 'UNIT_TEST_ONLY_NOT_REAL_REVIEW'}}


@pytest.mark.parametrize('mutation,reason', [
    (lambda c: c.update(synthetic=True), 'synthetic'),
    (lambda c: c.update(source_type='placeholder'), 'placeholder'),
    (lambda c: c.update(experiment_label='UNCERTAIN'), 'UNCERTAIN'),
    (lambda c: c.update(split_preregistered=False), 'preregistered'),
    (lambda c: c['provenance'].update(license_or_authorization=''), 'authorization'),
    (lambda c: c['provenance'].update(functional_check_status='FAILED'), 'functional'),
    (lambda c: c['annotation'].update(reviewer_b='TEST_ONLY_A'), 'second review'),
    (lambda c: c['annotation'].update(reviewer_a_type='AI'), 'human'),
    (lambda c: c['annotation'].update(independence_confirmed=False), 'independence'),
    (lambda c: c['annotation'].update(status='PENDING'), 'unresolved'),
    (lambda c: c.update(source_family_ids=['same', 'same']), 'distinct source families'),
    (lambda c: c['annotation'].update(independence_evidence=''), 'relationship evidence'),
    (lambda c: c['provenance'].update(template_status='UNDECLARED'), 'template'),
    (lambda c: c.update(source_type='ai_assisted', case_type='AI_REWRITE'), 'model_name'),
    (lambda c: c.update(case_type='VARIABLE_RENAME'), 'parent_source_ref'),
])
def test_quality_gates_do_not_silently_accept_missing_evidence(mutation, reason):
    case = reviewed_case()
    mutation(case)
    assert reason in ' '.join(case_readiness(case))


def test_empty_or_excluded_pool_is_not_formally_ready():
    case = reviewed_case()
    case['eligible_for_core_metrics'] = False
    report = assess({}, [case], {'errors': []}, b'{}')
    assert report['status'] == 'FORMAL_BLOCKED' and report['formalEligiblePairs'] == 0
    assert report['rows'][0]['selected'] is False


def test_declared_evidence_can_pass_but_is_not_authentication():
    cases = [reviewed_case(i, split, label) for i, (split, label) in enumerate([
        ('validation', 'INDEPENDENT'), ('validation', 'TRANSFORMED'), ('test', 'INDEPENDENT'), ('test', 'TRANSFORMED')])]
    config = b'{"unit_test":true}'
    manifest = {'evaluation_registration': {'status': 'FROZEN', 'config_sha256': hashlib.sha256(config).hexdigest(),
                                            'registered_at': '2026-10-11', 'reference': 'UNIT_TEST_ONLY'}}
    before = copy.deepcopy(cases)
    report = assess(manifest, cases, {'errors': []}, config)
    assert report['status'] == 'FORMAL_READY_DECLARED_EVIDENCE_REQUIRES_HUMAN_AUDIT'
    assert report['formalEligiblePairs'] == 4
    assert cases == before


@pytest.mark.parametrize('link', ['problem_id', 'source_id', 'source_family_ids', 'code_a_sha256'])
def test_connected_split_leakage_blocks_readiness(link):
    cases = [reviewed_case(0), reviewed_case(1, 'test')]
    cases[1][link] = copy.deepcopy(cases[0][link])
    report = assess({}, cases, {'errors': []}, b'{}')
    assert any('leakage' in b for b in report['formalBlockers'])
