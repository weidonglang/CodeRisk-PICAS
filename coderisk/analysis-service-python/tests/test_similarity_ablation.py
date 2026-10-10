"""Independent evaluation contracts; self-authored fixtures, never benchmark labels."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiment'))
from similarity_ablation import (average_precision, binary_metrics, evaluate, method_score, run,
                                 quality_blockers, recall_at_k, select_operating_point,
                                 validate_config, verify_isolation)


def config():
    return json.loads((ROOT / 'configs/experiments/similarity_ablation_v1.json').read_text())


def row(pair, split, label, value, **changes):
    result = {'pair_id': pair, 'split': split, 'label': label, 'problem_id': pair,
              'source_id': pair, 'group_id': pair, 'language': 'python', 'case_type': 'VARIABLE_RENAME',
              'problem_type': 'simple_io', 'raw': value, 'ast': value, 'canonical': value,
              'mapping': value, 'full': value, 'dynamic_threshold': .68,
              'code_a_sha256': pair + '-a', 'code_b_sha256': pair + '-b',
              'analysis_elapsed_ms': 1, 'warnings': ''}
    result.update(changes)
    return result


def rows():
    return [row('vp', 'validation', 'TRANSFORMED', .85), row('vn', 'validation', 'INDEPENDENT', .3),
            row('tp', 'test', 'TRANSFORMED', .8), row('tn', 'test', 'NATURAL_SIMILAR', .4)]


def test_frozen_matrix_has_singles_all_six_pairs_and_production_controls():
    cfg = config()
    validate_config(cfg)
    assert len(cfg['methods']) == 14
    assert sum(len(m.get('weights', {})) == 1 for m in cfg['methods']) == 4
    assert sum(len(m.get('weights', {})) == 2 for m in cfg['methods']) == 6
    assert {'PICAS_FIXED', 'PICAS_RULE_DYNAMIC', 'PICAS_DYNAMIC_OFFSET'} <= {m['name'] for m in cfg['methods']}


@pytest.mark.parametrize('weights', [{'raw': -1, 'ast': 2}, {'raw': float('nan')}, {'ir': 1}, {'raw': .4}])
def test_bad_or_experimental_weight_config_rejected(weights):
    cfg = config()
    cfg['methods'][0]['weights'] = weights
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_unavailable_feature_is_null_not_zero_or_raw_fallback_for_single_metric():
    sample = row('a', 'test', 'TRANSFORMED', .8, canonical=None)
    assert method_score(sample, config()['methods'][2]) is None
    assert method_score(sample, next(m for m in config()['methods'] if m['name'] == 'PICAS_FIXED')) == .8


def test_average_precision_groups_ties_and_is_input_order_invariant():
    samples = [row('p', 'test', 'TRANSFORMED', .8), row('n', 'test', 'INDEPENDENT', .8),
               row('p2', 'test', 'TRANSFORMED', .3)]
    assert average_precision(samples, [.8, .8, .3]) == pytest.approx(7 / 12)
    assert average_precision(list(reversed(samples)), [.3, .8, .8]) == pytest.approx(7 / 12)


def test_undefined_and_unknown_labels_are_not_invented_negatives():
    uncertain = row('u', 'test', 'UNCERTAIN', .9)
    assert average_precision([uncertain], [.9]) is None
    assert average_precision([row('n', 'test', 'INDEPENDENT', .9)], [.9]) is None
    result = binary_metrics([uncertain], [True])
    assert result['n'] == 0 and result['f1'] is None and result['fpr'] is None
    with pytest.raises(ValueError):
        average_precision([uncertain], [])


def test_test_scores_labels_cannot_change_threshold_or_low_fpr_selection():
    cfg, samples = config(), rows()
    method = cfg['methods'][0]
    selected = select_operating_point(samples, method, cfg)
    fpr = select_operating_point(samples, method, cfg, .05)
    samples[2].update(label='INDEPENDENT', raw=.1)
    samples[3].update(label='TRANSFORMED', raw=.99)
    assert selected == select_operating_point(samples, method, cfg)
    assert fpr == select_operating_point(samples, method, cfg, .05)
    assert fpr['validation_fpr'] <= .05


def test_insufficient_validation_labels_leave_threshold_metrics_unavailable():
    samples = [row('v', 'validation', 'INDEPENDENT', .2), row('t', 'test', 'TRANSFORMED', .8)]
    result = evaluate(samples, config())
    metric = next(m for m in result['metrics'] if m['method'] == 'RAW_ONLY' and m['scope'] == 'COMMON' and m['split'] == 'test')
    assert metric['f1'] is None and metric['threshold_status'] == 'INSUFFICIENT_VALIDATION_CLASSES'
    assert metric['pr_auc_ap_score'] is None


def test_common_support_prevents_method_specific_sample_advantage():
    samples = rows() + [row('missing', 'test', 'TRANSFORMED', .99, canonical=None, mapping=None)]
    result = evaluate(samples, config())
    common = [r for r in result['metrics'] if r['scope'] == 'COMMON' and r['split'] == 'test']
    assert {r['n_ranked'] for r in common} == {2}
    raw = next(r for r in result['metrics'] if r['scope'] == 'AVAILABLE' and r['split'] == 'test' and r['method'] == 'RAW_ONLY')
    assert raw['n_ranked'] == 3
    assert any(r['pair_id'] == 'missing' and r['method'] == 'CANONICAL_ONLY' and r['score'] is None for r in result['predictions'])


def test_recall_at_k_requires_declared_complete_query_pool():
    samples = rows()[2:]
    assert recall_at_k(samples, [r['raw'] for r in samples], 1)['value'] is None
    for sample in samples:
        sample.update(retrieval_query_id='q1', retrieval_pool_complete=True, query_source_sha256='anchor',
                      code_a_sha256='anchor', problem_id='retrieval-problem', retrieval_pool_size=2)
    assert recall_at_k(samples, [.9, .2], 1)['value'] == 1
    samples[1]['retrieval_pool_complete'] = False
    assert recall_at_k(samples, [.9, .2], 1)['value'] is None


def test_retrieval_cannot_silently_drop_unsupported_candidates():
    samples = rows()[2:]
    for sample in samples:
        sample.update(retrieval_query_id='q1', retrieval_pool_complete=True, query_source_sha256='anchor',
                      code_a_sha256='anchor', problem_id='retrieval-problem', retrieval_pool_size=2)
    assert recall_at_k(samples[:1], [.9], 1)['value'] is None
    samples[1].update(canonical=None, mapping=None)
    result = evaluate(rows()[:2] + samples, config())
    canonical = next(r for r in result['retrieval'] if r['method'] == 'CANONICAL_ONLY' and r['k'] == 1)
    assert canonical['value'] is None


def test_real_seed_runner_is_explicit_development_and_immutable(tmp_path):
    cfg = config()
    cfg['renameVariantsPerCase'] = 1
    config_path = tmp_path / 'config.json'
    config_path.write_text(json.dumps(cfg), encoding='utf-8')
    output = tmp_path / 'run'
    with pytest.raises(ValueError, match='Formal run blocked'):
        run(config_path, output)
    assert not output.exists()
    record = run(config_path, output, True)
    assert record['status'] == 'COMPLETED' and record['formalEligiblePairs'] == 0
    assert record['claimLevel'] == 'DEVELOPMENT_EXPLORATORY_NOT_BENCHMARK'
    for filename in ('scores.csv', 'metrics.csv', 'results.json', 'selection.json', 'failures.csv',
                     'borderline.csv', 'coverage.csv', 'retrieval.csv', 'rename_stability.csv', 'REPORT.md'):
        assert (output / filename).exists()
    with pytest.raises(FileExistsError):
        run(config_path, output, True)


@pytest.mark.parametrize('link', ['problem_id', 'source_id', 'source_family_ids', 'code_a_sha256'])
def test_transitive_group_leakage_is_fatal_even_in_development(link):
    samples = [dict(pair_id=str(i), split=split, problem_id=str(i), source_id=str(i), source_family_ids=[str(i)],
                    code_a_sha256=str(i) + 'a', code_b_sha256=str(i) + 'b')
               for i, split in enumerate(('validation', 'test'))]
    samples[1][link] = samples[0][link]
    with pytest.raises(ValueError, match='leakage'):
        verify_isolation(samples)


def test_synthetic_and_ai_reviewers_do_not_pass_formal_gate():
    case = dict(pair_id='a', synthetic=False, source_type='manual', eligible_for_core_metrics=True,
                split_preregistered=True, experiment_label='TRANSFORMED', source_family_ids=['family'],
                provenance={'license_or_authorization': 'self-authored'}, annotation={
                    'reviewer_a': 'r1', 'reviewer_b': 'r2', 'reviewer_a_type': 'AI', 'reviewer_b_type': 'HUMAN',
                    'independence_confirmed': True, 'status': 'AGREED', 'label': 'TRANSFORMED',
                    'label_basis': 'known rewrite', 'reviewed_at': '2026-10-10', 'functional_evidence': 'tests'})
    manifest = {'evaluation_registration': {'status': 'FROZEN', 'config_sha256': 'hash',
                                           'registered_at': '2026-10-10', 'reference': 'development protocol'}}
    assert quality_blockers([case], manifest, 'hash')
    case['annotation']['reviewer_a_type'] = 'HUMAN'
    assert not quality_blockers([case], manifest, 'hash')
    case['synthetic'] = True
    assert quality_blockers([case], manifest, 'hash')
