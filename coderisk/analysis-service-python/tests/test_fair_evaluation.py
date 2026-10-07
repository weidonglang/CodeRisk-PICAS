import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from research_protocol import connected_groups, formal_blockers, propose_split
from research_v4_dataset import load_research_dataset, validate_cases
from run_fair_evaluation import cluster_intervals, metrics, score, select_parameter
from research_v4_jplag import execute_jplag


def test_test_scores_and_labels_cannot_change_selected_threshold():
    rows = [{'split': 'validation', 'label': 'TRANSFORMED', 'full': .8},
            {'split': 'validation', 'label': 'INDEPENDENT', 'full': .4},
            {'split': 'test', 'label': 'TRANSFORMED', 'full': .1}]
    first = select_parameter(rows, 'FULL_FIXED', [.3, .5, .9])
    rows[-1].update(label='INDEPENDENT', full=1.0)
    assert first == select_parameter(rows, 'FULL_FIXED', [.3, .5, .9])
    assert first[0] == .5


def test_ablation_removes_both_canonical_signals_and_keeps_fallback():
    row = {'raw': .2, 'ast': .8, 'canonical': 1, 'mapping': 1, 'fusion_enabled': True}
    assert score(row, 'NO_CANONICAL_FIXED') == .5
    row.update(canonical=0, mapping=0)
    assert score(row, 'NO_CANONICAL_FIXED') == .5
    row['fusion_enabled'] = False
    assert score(row, 'NO_CANONICAL_FIXED') == .2


def test_undefined_metrics_are_not_perfect_or_zero_filled():
    result = metrics([{'label': 'INDEPENDENT'}], [False])
    assert result['precision'] is None and result['recall'] is None and result['f1'] is None
    assert result['natural_fpr'] is None and result['fpr'] == 0
    with pytest.raises(ValueError):
        select_parameter([{'split': 'validation', 'label': 'INDEPENDENT'}], 'FULL_FIXED', [.5])


def test_transitive_source_family_split_is_deterministic_and_indivisible():
    cases = [{'pair_id': str(i), 'problem_id': f'p{i}', 'source_id': f's{i}',
              'source_family_ids': [f'f{i}'], 'code_a_sha256': f'a{i}', 'code_b_sha256': f'b{i}'} for i in range(4)]
    cases[1]['source_family_ids'] = ['f0', 'f2']
    groups = connected_groups(cases)
    assert groups['0'] == groups['1'] == groups['2'] != groups['3']
    first = propose_split(cases, 7)
    assert first == propose_split(list(reversed(cases)), 7)
    assert len({r['proposed_split'] for r in first[:3]}) == 1
    assert not any(r['split_preregistered'] for r in first)


def test_real_loader_rejects_new_source_family_leakage():
    root = Path(__file__).resolve().parents[2]
    manifest, cases, _ = load_research_dataset(root / 'experiment/datasets/research-v4/dataset.json')
    cases = copy.deepcopy(cases)
    for split in ('validation', 'test'):
        next(case for case in cases if case['split'] == split)['source_family_ids'] = ['shared-original']
    result = validate_cases(manifest, cases)
    assert not result['valid']
    assert result['sourceFamilyOverlap'] == ['shared-original']
    assert formal_blockers(cases)


def test_group_bootstrap_is_repeatable_and_pairs_method_differences():
    rows = [{'group_id': str(i), 'label': label, 'full': value, 'dynamic_threshold': .5}
            for i, (label, value) in enumerate([('TRANSFORMED', .9), ('INDEPENDENT', .2), ('TRANSFORMED', .7)])]
    selected = {'FULL_FIXED': .5, 'FULL_DYNAMIC': 0}
    first = cluster_intervals(rows, selected, 7, 30)
    assert first == cluster_intervals(rows, selected, 7, 30)
    assert all(r['low'] == r['high'] == 0 for r in first if r['method'].startswith('DELTA') and r['valid_replicates'])


def test_jplag_process_failure_keeps_every_requested_pair(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a, 1, '', 'parse failed'))
    rows = [{'language': 'java', 'pairId': 'a', 'submissionA': 'left', 'submissionB': 'right'}]
    result, runs = execute_jplag(tmp_path, rows, Path('tool.jar'), Path('java'), 'test', 5)
    assert result[0]['resultStatus'] == 'RUN_FAILED'
    assert result[0]['predictedScore'] is None
    assert len(result) == 1 and runs[0]['exitCode'] == 1
