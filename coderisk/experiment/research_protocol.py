"""Leakage groups and a reviewable split proposal. Never edits the dataset."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research_v4_dataset import load_research_dataset


def connected_groups(cases: list[dict]) -> dict[str, str]:
    parents = list(range(len(cases)))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    owners = {}
    for index, case in enumerate(cases):
        families = case.get('source_family_ids', [])
        if not isinstance(families, list) or any(not isinstance(x, str) or not x.strip() for x in families):
            raise ValueError('source_family_ids must be a list of nonempty identifiers')
        keys = [('problem', case['problem_id']), ('source', case['source_id'])]
        keys += [('family', value) for value in families]
        keys += [('hash', case[key]) for key in ('code_a_sha256', 'code_b_sha256')]
        for key in keys:
            if key in owners:
                parents[root(index)] = root(owners[key])
            else:
                owners[key] = index
    members = {}
    for index, case in enumerate(cases):
        members.setdefault(root(index), []).append(case['pair_id'])
    names = {key: 'G-' + hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()[:12]
             for key, ids in members.items()}
    return {case['pair_id']: names[root(index)] for index, case in enumerate(cases)}


def propose_split(cases: list[dict], seed: int, validation_fraction: float = 0.3) -> list[dict]:
    if not 0 < validation_fraction < 1:
        raise ValueError('validation_fraction must be strictly between 0 and 1')
    groups = connected_groups(cases)
    unique = sorted(set(groups.values()), key=lambda value: hashlib.sha256(f'{seed}:{value}'.encode()).digest())
    if len(unique) < 2:
        raise ValueError('At least two independent connected groups are required')
    count = min(len(unique) - 1, max(1, round(len(unique) * validation_fraction)))
    validation = set(unique[:count])
    return [{'pair_id': case['pair_id'], 'group_id': groups[case['pair_id']],
             'proposed_split': 'validation' if groups[case['pair_id']] in validation else 'test',
             'split_preregistered': False} for case in sorted(cases, key=lambda case: case['pair_id'])]


def formal_blockers(cases: list[dict]) -> list[str]:
    blockers = []
    for case in cases:
        if not case['eligible_for_core_metrics']:
            continue
        reasons = []
        if case['synthetic'] or case['source_type'] == 'placeholder':
            reasons.append('synthetic/placeholder')
        if case.get('split_preregistered') is not True:
            reasons.append('split not preregistered')
        annotation = case.get('annotation', {})
        if not isinstance(annotation, dict):
            annotation = {}
        required = ('reviewer_a', 'reviewer_b', 'label_basis', 'reviewed_at', 'functional_evidence')
        if any(not isinstance(annotation.get(key), str) or not annotation[key].strip() for key in required):
            reasons.append('incomplete annotation evidence')
        if annotation.get('reviewer_a') == annotation.get('reviewer_b'):
            reasons.append('independent second review missing')
        if annotation.get('status') != 'AGREED' or annotation.get('label') != case['experiment_label']:
            reasons.append('unresolved annotation or label mismatch')
        if len(case.get('source_family_ids', [])) < 1:
            reasons.append('source families missing')
        if not case.get('provenance', {}).get('license_or_authorization'):
            reasons.append('authorization missing')
        if reasons:
            blockers.append(f"{case['pair_id']}: {', '.join(reasons)}")
    return blockers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=20261008)
    parser.add_argument('--validation-fraction', type=float, default=0.3)
    args = parser.parse_args()
    manifest, cases, _ = load_research_dataset(args.manifest)
    proposal = {'status': 'REVIEW_REQUIRED_NOT_PREREGISTERED', 'dataset': manifest['dataset_version'],
                'seed': args.seed, 'validationFractionByGroup': args.validation_fraction,
                'rows': propose_split(cases, args.seed, args.validation_fraction)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(proposal, handle, ensure_ascii=False, indent=2)
    print(args.output)


if __name__ == '__main__':
    main()
