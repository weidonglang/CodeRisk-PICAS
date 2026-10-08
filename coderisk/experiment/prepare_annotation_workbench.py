"""Prepare blinded review queues and an offline HTML workbench; leave all relation labels unknown."""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
import json
from datetime import datetime
from pathlib import Path

from acquire_public_datasets import digest, write_json, write_rows
from review_public_data import ROOT, jsonl

LABELS = {'TRANSFORMED', 'SIMILAR', 'INDEPENDENT', 'NATURAL_SIMILAR', 'UNCERTAIN'}


def stable_order(rows, key):
    return sorted(rows, key=lambda r: digest(str(r[key]).encode()))


def make_candidate(dataset, problem, left, right, source_pair_id=None):
    if left['language'] != right['language']:
        raise ValueError('Review pairs must share a language')
    identity = [dataset, problem, left['code_sha256_bytes'], right['code_sha256_bytes'], source_pair_id]
    return {'review_id': 'R-' + digest(json.dumps(identity).encode())[:20], 'dataset': dataset,
            'problem_id': problem, 'language': left['language'], 'source_pair_id': source_pair_id,
            'source_a': left, 'source_b': right, 'experiment_label': 'UNCERTAIN',
            'annotation_status': 'AWAITING_TWO_INDEPENDENT_REVIEWS', 'eligible_for_core_metrics': False,
            'selection_uses_detector_scores': False, 'published_label_shown': False}


def candidates(public: Path, quality: Path):
    records = jsonl(quality / 'source_quality_registry.jsonl')
    ad = {r['source_id']: r for r in records if r['dataset'] == 'ad2022'}
    con = {r['code_path']: r for r in records if r['dataset'] == 'conplag-v3' and r['view'] == 'version_1'}
    result, labels = [], []
    for row in jsonl(public / 'ad2022/candidate_pairs.jsonl'):
        result.append(make_candidate('ad2022', row['question_id'], ad[row['submission_a']], ad[row['submission_b']], row['pair_id']))
    for row in jsonl(public / 'conplag-v3/published_pairs.jsonl'):
        left, right = row['files']['version_1']
        a = 'data/public-datasets/' + public.name + '/conplag-v3/' + left['code_path']
        b = 'data/public-datasets/' + public.name + '/conplag-v3/' + right['code_path']
        # A repeated byte version may have its representative path in another pair directory.
        def lookup(path, file):
            return con.get(path) or next(r for r in records if r['dataset'] == 'conplag-v3' and r['view'] == 'version_1'
                                        and r['source_id'] == 'CONPLAG-' + file['submission_id'] and r['code_sha256_bytes'] == file['code_sha256_bytes'])
        item = make_candidate('conplag-v3', row['problem_id'], lookup(a, left), lookup(b, right), row['pair_id'])
        result.append(item)
        labels.append({'review_id': item['review_id'], 'published_verdict': row['published_verdict'],
                       'annotation_scope': 'PUBLISHER_SINGLE_ANNOTATOR_NOT_LOCAL_DOUBLE_REVIEW'})
    groups = defaultdict(list)
    for row in records:
        if row['dataset'] == 'codenet' and row['language'] == 'c' and row['syntax_parsed'] and not row['cpp_syntax_hints']:
            groups[('codenet', row['problem_id'])].append(row)
        elif row['dataset'] == 'mdn' and row['syntax_parsed']:
            groups[('mdn', row['problem_id'])].append(row)
    for (dataset, problem), rows in sorted(groups.items()):
        unique = {r['code_sha256_text']: r for r in stable_order(rows, 'record_id')}
        rows = stable_order(list(unique.values()), 'record_id')
        if len(rows) >= 2:
            result.append(make_candidate(dataset, problem, rows[0], rows[1]))
    return stable_order(result, 'review_id'), labels


def first_batch(rows):
    selected, seen = [], Counter()
    for row in rows:
        if row['dataset'] == 'conplag-v3':
            key, maximum = (row['dataset'], row['problem_id']), 1
        else:
            key, maximum = (row['dataset'], row['language']), 6
        if seen[key] < maximum:
            selected.append(row)
            seen[key] += 1
    return selected


def script_json(payload):
    # Source HTML/Java strings cannot terminate the script block; UI only uses textContent.
    return json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def render_workbench(rows, manifest_hash):
    public_rows = []
    for row in rows:
        public_rows.append({'review_id': row['review_id'], 'dataset': row['dataset'], 'problem_id': row['problem_id'],
                            'language': row['language'], 'hash_a': row['source_a']['code_sha256_bytes'],
                            'hash_b': row['source_b']['code_sha256_bytes'],
                            'code_a': (ROOT / row['source_a']['code_path']).read_text(encoding='utf-8'),
                            'code_b': (ROOT / row['source_b']['code_path']).read_text(encoding='utf-8'),
                            'functional_evidence_a': row['source_a']['functional_evidence'],
                            'functional_evidence_b': row['source_b']['functional_evidence']})
    template = Path(__file__).with_name('annotation_workbench.html').read_text(encoding='utf-8')
    return template.replace('/*REVIEW_PAYLOAD*/', script_json({'manifest_sha256': manifest_hash, 'rows': public_rows}))


def merge_reviews(manifest, left, right):
    expected = digest(manifest.read_bytes())
    rows = jsonl(manifest)
    reviewers = []
    for file in (left, right):
        value = json.loads(file.read_text(encoding='utf-8'))
        if not isinstance(value, dict) or value.get('manifest_sha256') != expected or not isinstance(value.get('reviewer_id'), str) or not value['reviewer_id'].strip():
            raise ValueError('Review manifest hash or reviewer ID invalid')
        entries = value.get('annotations', [])
        if not isinstance(entries, list) or any(not isinstance(r, dict) or not isinstance(r.get('review_id'), str) for r in entries):
            raise ValueError('Annotations must be a list of review objects')
        indexed = {r['review_id']: r for r in entries}
        if len(indexed) != len(entries) or set(indexed) - {r['review_id'] for r in rows}:
            raise ValueError('Duplicate or unknown review IDs')
        reviewers.append((value['reviewer_id'].strip(), indexed))
    if reviewers[0][0] == reviewers[1][0]:
        raise ValueError('Two distinct reviewer IDs required')
    merged = []
    def complete(entry, row):
        if not entry or entry.get('label') not in LABELS or not isinstance(entry.get('basis'), str) or not entry['basis'].strip():
            return False
        try:
            timestamp = datetime.fromisoformat(entry.get('reviewed_at', '').replace('Z', '+00:00'))
            if timestamp.tzinfo is None:
                return False
        except (ValueError, TypeError, AttributeError):
            return False
        return entry.get('hash_a') == row['source_a']['code_sha256_bytes'] and entry.get('hash_b') == row['source_b']['code_sha256_bytes']
    for row in rows:
        entries = [r[1].get(row['review_id']) for r in reviewers]
        ready = all(complete(r, row) for r in entries)
        agreed = ready and entries[0]['label'] == entries[1]['label']
        merged.append({'review_id': row['review_id'], 'reviewer_ids': [r[0] for r in reviewers],
                       'reviews': entries, 'status': 'AGREED' if agreed else 'DISAGREED' if ready else 'INCOMPLETE',
                       'final_label': entries[0]['label'] if agreed else 'UNCERTAIN',
                       'eligible_for_core_metrics': False,
                       'remaining_requirements': ['source/functional evidence review', 'leakage-free split and frozen study protocol']})
    return merged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-intake', type=Path, default=ROOT / 'data/public-datasets/public-intake-20261008')
    parser.add_argument('--quality', type=Path, default=ROOT / 'experiment/evidence/data-quality-20261009')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--merge', nargs=2, type=Path)
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output directory')
    args.output.mkdir(parents=True)
    if args.merge:
        if not args.manifest:
            parser.error('--manifest required with --merge')
        merged = merge_reviews(args.manifest, *args.merge)
        write_rows(args.output / 'merged_reviews.jsonl', merged)
        write_json(args.output / 'merge_summary.json', dict(Counter(r['status'] for r in merged)))
        return
    rows, labels = candidates(args.public_intake, args.quality)
    batch = first_batch(rows)
    write_rows(args.output / 'candidate_manifest.jsonl', rows)
    write_rows(args.output / 'publisher_labels_do_not_open_during_blind_review.jsonl', labels)
    write_rows(args.output / 'first_batch_manifest.jsonl', batch)
    manifest_hash = digest((args.output / 'first_batch_manifest.jsonl').read_bytes())
    (args.output / 'review.html').write_text(render_workbench(batch, manifest_hash), encoding='utf-8')
    summary = {'status': 'UNLABELLED_REVIEW_QUEUE', 'candidate_pairs': len(rows), 'first_batch_pairs': len(batch),
               'first_batch_language_counts': dict(Counter(r['language'] for r in batch)),
               'first_batch_manifest_sha256': manifest_hash, 'detector_scores_shown': False,
               'publisher_labels_shown': False, 'core_metric_eligible_pairs': 0}
    write_json(args.output / 'review_summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
