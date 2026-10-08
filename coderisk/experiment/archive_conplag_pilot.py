"""Validate and archive metadata-only pilot evidence and static scientific plots."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil

from acquire_public_datasets import digest, write_json
from review_public_data import jsonl
from run_published_conplag import METHODS, published_metrics


def archive(source, output):
    summary = json.loads((source / 'run_summary.json').read_text(encoding='utf-8'))
    if summary['status'] != 'EXPLORATORY_EXTERNAL_LABEL_RESULTS' or (source / 'RUN_FAILED.json').exists():
        raise ValueError('A completed exploratory run is required')
    protocol_bytes = (source / 'protocol_snapshot.json').read_bytes()
    if digest(protocol_bytes) != summary['protocol_sha256']:
        raise ValueError('Protocol snapshot hash mismatch')
    # Recompute every reported confusion table from saved pair scores before export.
    for view in summary['views']:
        scores = jsonl(source / view / 'picas_scores.jsonl')
        baseline = {r['pairId']: r for r in jsonl(source / view / 'jplag_scores.jsonl')}
        if len(scores) != summary['views'][view]['pair_count'] or len(baseline) != len(scores):
            raise ValueError('Score or baseline pair coverage mismatch')
        common = [{**r, 'JPLAG_FIXED': baseline[r['pair_id']]['predictedScore']} for r in scores
                  if baseline[r['pair_id']]['resultStatus'] == 'MATCHED']
        evaluation = json.loads((source / view / 'evaluation.json').read_text(encoding='utf-8'))
        for cohort, rows in [('all_picas_pairs', scores), ('common_cohort', common)]:
            for table in (evaluation[cohort] or {}).get('tables', []):
                actual = published_metrics([r for r in rows if r['split'] == table['split']], table['method'], table['threshold'])
                if any(actual[key] != table[key] for key in actual):
                    raise ValueError('Saved statistics do not match pair scores')
    output.mkdir(parents=True)
    # Explicit allowlist: native reports/archives and input directories may contain raw source.
    allowlist = [source / name for name in ('run_summary.json', 'run_start.json', 'protocol_snapshot.json')]
    for view in summary['views']:
        allowlist.extend(source / view / name for name in ('picas_scores.jsonl', 'jplag_scores.jsonl', 'jplag_runs.json', 'evaluation.json'))
        for pattern in ('*/native/java/results/results.csv', '*/native/java/stdout.txt', '*/native/java/stderr.txt'):
            allowlist.extend(sorted((source / view / 'jplag').glob(pattern)))
    for file in allowlist:
        target = output / file.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
    all_tables = []
    for view in summary['views']:
        evaluation = json.loads((output / view / 'evaluation.json').read_text(encoding='utf-8'))
        for key in ('all_picas_pairs', 'common_cohort'):
            all_tables.extend({'view': view, **r} for r in (evaluation[key] or {}).get('tables', []))
    with (output / 'metric_tables.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(all_tables[0]))
        writer.writeheader()
        writer.writerows(all_tables)
    plot(output)
    inventory = [{'path': f.relative_to(output).as_posix(), 'sha256': digest(f.read_bytes()), 'size': f.stat().st_size}
                 for f in sorted(output.rglob('*')) if f.is_file()]
    write_json(output / 'artifact_inventory.json', {'pair_tables_recomputed_and_equal': True, 'raw_sources_included': False,
        'files': inventory, 'archiver_sha256': digest(Path(__file__).read_bytes())})
    print(json.dumps({'output': str(output), 'files': len(inventory), 'tables_verified': len(all_tables)}))


def plot(root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout='constrained')
    methods = [*METHODS, 'JPLAG_FIXED']
    labels = ['Fusion', 'No canonical', 'Raw token', 'Canonical', 'JPlag']
    for column, view in enumerate(('version_1', 'version_2')):
        result = json.loads((root / view / 'evaluation.json').read_text(encoding='utf-8'))['common_cohort']
        tables = {r['method']: r for r in result['tables'] if r['split'] == 'test'}
        intervals = {(r['method'], r['metric']): r for r in result['test_cluster_intervals']}
        for row, metric in enumerate(('f1', 'fpr')):
            ax = axes[row, column]
            values = [tables[m][metric] for m in methods]
            ax.bar(range(5), values, color=['#2864a5', '#65a0cd', '#8eacbd', '#aaba8a', '#d99a50'], width=.65)
            for i, method in enumerate(methods):
                ci = intervals[(method, metric)]
                ax.vlines(i, ci['low'], ci['high'], color='#222222', linewidth=1.5)
                ax.hlines([ci['low'], ci['high']], i-.1, i+.1, color='#222222')
            ax.set_xticks(range(5), labels, rotation=15)
            ax.set_ylim(0, 1 if metric == 'f1' else .4)
            ax.set_ylabel('F1' if metric == 'f1' else 'False positive rate')
            ax.set_title(f'{"Original" if view == "version_1" else "Publisher template-free"} / test n={tables[methods[0]]["n"]}')
            ax.grid(axis='y', alpha=.2)
            ax.set_axisbelow(True)
    fig.suptitle('ConPlag published-label pilot: validation-selected fixed thresholds\n95% problem-cluster bootstrap intervals; exploratory, conditional on selected thresholds', fontsize=12)
    for extension in ('png', 'svg', 'pdf'):
        fig.savefig(root / ('test_comparison.' + extension), dpi=220, facecolor='white')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output directory')
    archive(args.input, args.output)


if __name__ == '__main__':
    main()
