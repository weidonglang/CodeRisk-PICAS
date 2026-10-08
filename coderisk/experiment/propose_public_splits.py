"""Conservative source/topic/hash connected components. Proposals never imply independence."""
import argparse
from collections import defaultdict, Counter
import json
from pathlib import Path
import re

from acquire_public_datasets import digest, write_json
from review_public_data import ROOT, jsonl


def components(rows, keys):
    parent = list(range(len(rows)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner = {}
    for index, row in enumerate(rows):
        for key in keys(row):
            if key in owner:
                parent[root(index)] = root(owner[key])
            else:
                owner[key] = index
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        groups[root(index)].append(row['review_id'])
    names = {index: 'G-' + digest('\n'.join(sorted(ids)).encode())[:16] for index, ids in groups.items()}
    return {row['review_id']: names[root(i)] for i, row in enumerate(rows)}


def title_key(title):
    return re.sub(r'\s+', ' ', re.sub(r'[\[(](?:Java|Python)[\])]', '', title, flags=re.I)).strip().casefold()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--quality', type=Path, required=True)
    parser.add_argument('--public-intake', type=Path, default=ROOT / 'data/public-datasets/public-intake-20261008')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output must be new')
    rows = jsonl(args.review / 'candidate_manifest.jsonl')
    quality = jsonl(args.quality / 'source_quality_registry.jsonl')
    family_hashes = defaultdict(set)
    for source in quality:
        if source['source_family_id']:
            family_hashes[source['source_family_id']].add(source['code_sha256_text'])
    topics = {r['question_id']: title_key(r['upstream_fields'].get('title_eng', r['question_id']))
              for r in jsonl(args.public_intake / 'ad2022/questions.jsonl')}
    def keys(row):
        result = [('problem', row['problem_id'])]
        if row['dataset'] == 'ad2022':
            result.append(('ad-title-provisional', topics[row['problem_id']]))
        for side in ('source_a', 'source_b'):
            source = row[side]
            result += [('source', source['dataset'], source['source_id']), ('hash', source['code_sha256_text'])]
            if source['source_family_id']:
                result.append(('family', source['source_family_id']))
                result.extend(('hash', h) for h in family_hashes[source['source_family_id']])
        return result
    proposals, summary = [], {}
    for dataset in sorted({r['dataset'] for r in rows}):
        subset = [r for r in rows if r['dataset'] == dataset]
        groups = components(subset, keys)
        unique = sorted(set(groups.values()), key=lambda value: digest(('20261009:' + value).encode()))
        validation = set(unique[:max(1, round(len(unique) * .3))]) if len(unique) >= 2 else set()
        for row in subset:
            proposals.append({'review_id': row['review_id'], 'dataset': dataset, 'group_id': groups[row['review_id']],
                              'proposed_split': ('validation' if groups[row['review_id']] in validation else 'test') if len(unique) >= 2 else 'UNSPLITTABLE',
                              'split_preregistered': False, 'relationship_label': 'UNCERTAIN',
                              'author_independence_verified': False})
        summary[dataset] = {'candidate_pairs': len(subset), 'connected_groups': len(unique),
                            'split_counts': dict(Counter(r['proposed_split'] for r in proposals if r['dataset'] == dataset)),
                            'status': 'PROPOSAL_REQUIRES_REVIEW' if len(unique) >= 2 else 'NO_SAFE_TWO_WAY_SPLIT'}
    write_json(args.output, {'status': 'REVIEW_REQUIRED_NOT_FROZEN', 'client_date': '2026-10-09',
                            'grouping': 'same problem, provisional exact normalized AD title, known source/family, raw/template-free text hashes',
                            'seed': 20261009, 'by_dataset': summary, 'rows': proposals,
                            'unknown_authors_are_not_assumed_independent': True,
                            'compiler_and_relation_labels_pending': True})
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
