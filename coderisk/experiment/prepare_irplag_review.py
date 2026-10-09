"""Prepare score-blind IR-Plag review materials, preserving publisher labels separately."""
from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path

from acquire_irplag import ROOT, verify
from acquire_public_datasets import digest, write_json, write_rows
from prepare_annotation_workbench import make_candidate, render_workbench, stable_order


def prepare(intake: Path, output: Path):
    verify(intake)
    records = [json.loads(line) for line in (intake/'source_registry.jsonl').read_text(encoding='utf-8').splitlines()]
    pairs = [json.loads(line) for line in (intake/'published_pairs.jsonl').read_text(encoding='utf-8').splitlines()]
    tasks = {r['problem_id']:r['summary'] for r in json.loads((intake/'manifest.json').read_text(encoding='utf-8'))['tasks']}
    sources = {r['source_id']:{**r, 'code_path':(intake/r['code_path']).relative_to(ROOT).as_posix(),
        'functional_evidence':'仅发布者编译说明；未本地执行，可能有输出错误。题意摘要：'+tasks[r['problem_id']]} for r in records}
    grouped = defaultdict(list)
    for row in pairs:
        if not row['public_label_disputed']:
            grouped[(row['problem_id'],row['published_verdict'])].append(row)
    selected = [p for key,group in sorted(grouped.items()) for p in stable_order(group,'pair_id')[:3]]
    selected += [p for p in pairs if p['public_label_disputed']]
    review = [make_candidate('irplag',p['problem_id'],sources[p['source_a']],sources[p['source_b']],p['pair_id']) for p in selected]
    # The committed blind manifest carries IDs and hashes only, not paths or categories revealing labels.
    blind = [{k:r[k] for k in ('review_id','dataset','problem_id','language','source_pair_id','experiment_label','annotation_status','eligible_for_core_metrics','selection_uses_detector_scores','published_label_shown')}
             | {'hash_a':r['source_a']['code_sha256_bytes'],'hash_b':r['source_b']['code_sha256_bytes']} for r in review]
    write_rows(output/'blind_batch.jsonl',blind)
    secret = [{**p,'review_id':r['review_id']} for p,r in zip(selected,review)]
    write_rows(output/'publisher_labels_for_adjudicator.jsonl',secret)
    # Existing merger needs source hashes; this local manifest and self-contained HTML remain ignored.
    local = intake/'review'
    local_manifest = local/'review_manifest.jsonl'
    if local_manifest.exists():
        existing = [json.loads(line) for line in local_manifest.read_text(encoding='utf-8').splitlines()]
        if existing != review:
            raise ValueError('Existing local review manifest differs; use a fresh intake directory')
    else:
        write_rows(local_manifest,review)
    manifest_hash = digest((local/'review_manifest.jsonl').read_bytes())
    html = render_workbench(review,manifest_hash)
    html_path = local/'workbench.html'
    if html_path.exists() and html_path.read_text(encoding='utf-8') != html:
        raise ValueError('Existing workbench differs; preserve it and use a fresh intake directory')
    if not html_path.exists():
        html_path.write_text(html,encoding='utf-8')
    write_json(output/'review_preparation.json',{
        'review_pairs':len(review),'regular_per_task_per_published_class':3,'known_disputes':10,
        'local_human_reviews':0,'review_labels':'UNCERTAIN until actual reviewers submit evidence',
        'selection_uses_detector_scores':False,'blind_batch_sha256':digest((output/'blind_batch.jsonl').read_bytes()),
        'local_manifest_sha256':manifest_hash,'local_workbench_path':str(local/'workbench.html'),
        'note':'Adjudicator label file must not be shown before blind reviews; source category/path hidden in HTML.'})
    return len(review)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--intake',type=Path,default=ROOT/'data/public-datasets/irplag-20261009')
    parser.add_argument('--output',type=Path,default=ROOT/'experiment/evidence/irplag-intake-20261009')
    args=parser.parse_args()
    print(json.dumps({'review_pairs_prepared':prepare(args.intake.resolve(),args.output.resolve())}))
