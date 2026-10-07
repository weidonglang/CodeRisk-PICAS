"""Validation-only selection, controlled ablations and matched JPlag evaluation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis-service-python'))

from app.analyzers.token_similarity import analyze_token_pair  # noqa: E402
from research_protocol import connected_groups, formal_blockers  # noqa: E402
from research_v4_dataset import POSITIVE_LABELS, load_research_dataset  # noqa: E402
from research_v4_jplag import DEFAULT_JAR, DEFAULT_JAVA, execute_jplag, prepare_inputs  # noqa: E402
from run_research_v4 import _request  # noqa: E402

METHODS = ('FULL_FIXED', 'FULL_DYNAMIC', 'NO_CANONICAL_FIXED', 'NO_CANONICAL_DYNAMIC',
           'RAW_FIXED', 'CANONICAL_FIXED', 'FULL_DYNAMIC_PRODUCTION')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def metrics(rows: list[dict], predictions: list[bool]) -> dict:
    if len(rows) != len(predictions):
        raise ValueError('Prediction count mismatch')
    tp = fp = tn = fn = natural_fp = natural_n = 0
    for row, predicted in zip(rows, predictions):
        positive = row['label'] in POSITIVE_LABELS
        tp += int(positive and predicted)
        fn += int(positive and not predicted)
        fp += int(not positive and predicted)
        tn += int(not positive and not predicted)
        if row['label'] == 'NATURAL_SIMILAR':
            natural_n += 1
            natural_fp += int(predicted)
    ratio = lambda numerator, denominator: numerator / denominator if denominator else None
    return {'n': len(rows), 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
            'precision': ratio(tp, tp + fp), 'recall': ratio(tp, tp + fn),
            'f1': ratio(2 * tp, 2 * tp + fp + fn), 'fpr': ratio(fp, fp + tn),
            'natural_n': natural_n, 'natural_fpr': ratio(natural_fp, natural_n)}


def score(row: dict, method: str) -> float:
    if method == 'JPLAG_FIXED':
        return row['jplag']
    if method.startswith('NO_CANONICAL'):
        # Remove canonical AND mapping signals. Renormalize retained .20/.20.
        return 0.5 * row['raw'] + 0.5 * row['ast'] if row['fusion_enabled'] else row['raw']
    if method == 'RAW_FIXED':
        return row['raw']
    if method == 'CANONICAL_FIXED':
        return row['canonical'] if row['fusion_enabled'] else row['raw']
    return row['full']


def threshold(row: dict, method: str, parameter: float) -> float:
    return min(0.95, max(0.50, row['dynamic_threshold'] + parameter)) if 'DYNAMIC' in method else parameter


def predict(rows: list[dict], method: str, parameter: float) -> list[bool]:
    return [score(row, method) >= threshold(row, method, parameter) for row in rows]


def select_parameter(rows: list[dict], method: str, candidates: list[float]) -> tuple[float, list[dict]]:
    validation = [row for row in rows if row['split'] == 'validation']
    if not any(r['label'] in POSITIVE_LABELS for r in validation) or not any(r['label'] not in POSITIVE_LABELS for r in validation):
        raise ValueError('Threshold selection requires positive and negative validation examples')
    if not candidates or any(not math.isfinite(x) for x in candidates):
        raise ValueError('Finite, nonempty candidate parameters required')
    sweep = [{'method': method, 'parameter': p, **metrics(validation, predict(validation, method, p))}
             for p in sorted(set(candidates))]
    def objective(row):
        # Max F1, then lower FPR. Dynamic ties prefer the unchanged rule.
        p = row['parameter']
        return (row['f1'], -row['fpr'], -abs(p) if 'DYNAMIC' in method else p, p)
    return max(sweep, key=objective)['parameter'], sweep


def cluster_intervals(rows: list[dict], selected: dict[str, float], seed: int, repetitions: int) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[row['group_id']].append(row)
    keys = sorted(groups)
    if len(keys) < 2:
        return [{'method': method, 'metric': 'all', 'low': None, 'high': None,
                 'groups': len(keys), 'valid_replicates': 0} for method in selected]
    rng = random.Random(seed)
    samples = defaultdict(list)
    for _ in range(repetitions):
        sample = [row for _ in keys for row in groups[rng.choice(keys)]]
        current = {method: metrics(sample, predict(sample, method, parameter)) for method, parameter in selected.items()}
        for method, result in current.items():
            for key in ('f1', 'recall', 'fpr', 'natural_fpr'):
                if result[key] is not None:
                    samples[(method, key)].append(result[key])
        if 'FULL_DYNAMIC' in current and 'FULL_FIXED' in current:
            for key in ('f1', 'recall', 'fpr', 'natural_fpr'):
                a, b = current['FULL_DYNAMIC'][key], current['FULL_FIXED'][key]
                if a is not None and b is not None:
                    samples[('DELTA_DYNAMIC_MINUS_FIXED', key)].append(a - b)
    result = []
    methods = list(selected) + (['DELTA_DYNAMIC_MINUS_FIXED'] if 'FULL_DYNAMIC' in selected and 'FULL_FIXED' in selected else [])
    for method in methods:
        for metric in ('f1', 'recall', 'fpr', 'natural_fpr'):
            values = sorted(samples[(method, metric)])
            result.append({'method': method, 'metric': metric,
                           'low': values[math.floor((len(values) - 1) * .025)] if values else None,
                           'high': values[math.ceil((len(values) - 1) * .975)] if values else None,
                           'groups': len(keys), 'valid_replicates': len(values)})
    return result


def evaluate(rows: list[dict], config: dict, methods=METHODS) -> dict:
    selected, sweeps = {}, []
    for method in methods:
        candidates = [0.0] if method == 'FULL_DYNAMIC_PRODUCTION' else config['dynamicOffsets'] if 'DYNAMIC' in method else config['fixedThresholds']
        selected[method], sweep = select_parameter(rows, method, candidates)
        sweeps.extend(sweep)
    test = [r for r in rows if r['split'] == 'test']
    if not test:
        raise ValueError('Independent test partition is empty')
    results, predictions = [], []
    for method, parameter in selected.items():
        for split in ('validation', 'test'):
            subset = [r for r in rows if r['split'] == split]
            results.append({'method': method, 'split': split, 'parameter': parameter,
                            **metrics(subset, predict(subset, method, parameter))})
        for row in test:
            predicted = score(row, method) >= threshold(row, method, parameter)
            predictions.append({'pair_id': row['pair_id'], 'method': method,
                                'label': row['label'], 'score': score(row, method),
                                'threshold': threshold(row, method, parameter), 'predicted': predicted,
                                'correct': predicted == (row['label'] in POSITIVE_LABELS)})
    subgroups = []
    for key in ('language', 'case_type', 'problem_type', 'fusion_enabled'):
        for value in sorted({str(r[key]) for r in test}):
            subset = [r for r in test if str(r[key]) == value]
            for method, parameter in selected.items():
                subgroups.append({'dimension': key, 'value': value, 'method': method,
                                  **metrics(subset, predict(subset, method, parameter))})
    return {'selected': selected, 'validation_sweep': sweeps, 'metrics': results,
            'predictions': predictions, 'subgroups': subgroups,
            'intervals': cluster_intervals(test, selected, config['seed'], config['bootstrapReplicates'])}


def export_evaluation(output: Path, result: dict):
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'selected_parameters.json', {'selectionSplit': 'validation', 'testUsedForSelection': False,
               'objective': 'max F1, min FPR, then closest-to-zero offset or highest fixed threshold',
               'parameters': result['selected']})
    for name in ('validation_sweep', 'metrics', 'predictions', 'subgroups', 'intervals'):
        write_csv(output / f'{name}.csv', result[name])
    write_csv(output / 'failures.csv', [r for r in result['predictions'] if not r['correct']])


def plot_results(output: Path, result: dict, label: str):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt'] = 'coderisk-fair-v1'
    rows = [r for r in result['metrics'] if r['split'] == 'test']
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), layout='constrained')
    for axis, metric in zip(axes, ('f1', 'fpr')):
        values = [r[metric] if r[metric] is not None else 0 for r in rows]
        bars = axis.barh([r['method'] for r in rows], values, color='#276b8a')
        for bar, row in zip(bars, rows):
            text = f"{row[metric]:.3f}" if row[metric] is not None else 'N/A'
            axis.text(bar.get_width() + .015, bar.get_y() + bar.get_height()/2, text, va='center', fontsize=8)
        axis.set_xlim(0, 1.15)
        axis.set_title(f'{metric.upper()} (test)')
        axis.invert_yaxis()
    figure.suptitle(label + '\nObserved subset metrics; no population superiority claim', fontsize=12)
    figure.savefig(output / 'comparison.png', dpi=160)
    figure.savefig(output / 'comparison.svg', metadata={'Date': None})
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/experiments/fair_v1.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-development', action='store_true')
    parser.add_argument('--jplag-jar', type=Path, default=DEFAULT_JAR)
    parser.add_argument('--java', type=Path, default=DEFAULT_JAVA)
    parser.add_argument('--skip-jplag', action='store_true')
    args = parser.parse_args()
    args.output = args.output.resolve()
    config_bytes = args.config.read_bytes()
    config = json.loads(config_bytes)
    if config['templateMode'] != 'NONE' or config['jplagNormalization'] is not False:
        raise ValueError('This protocol currently supports NONE template mode and JPlag normalization disabled')
    if config['bootstrapReplicates'] < 1:
        raise ValueError('Positive bootstrap replicate count required')
    if any(not 0 <= x <= 1.000001 for x in config['fixedThresholds']):
        raise ValueError('Fixed thresholds outside score range')
    manifest, cases, validation = load_research_dataset(ROOT / config['datasetManifest'])
    blockers = formal_blockers(cases)
    registration = manifest.get('evaluation_registration', {})
    if registration.get('config_sha256') != digest(config_bytes) or registration.get('status') != 'FROZEN' or not registration.get('registered_at') or not registration.get('reference'):
        blockers.append('Dataset lacks a frozen, dated registration matching this configuration')
    if blockers and not args.allow_development:
        raise ValueError('Formal run blocked; use new verified data or explicitly --allow-development: ' + '; '.join(blockers[:5]))
    if not args.skip_jplag and (not args.java.is_file() or not args.jplag_jar.is_file()):
        raise FileNotFoundError('Java 21+ executable and JPlag jar required, or use --skip-jplag')
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'config.json', config)
    write_json(args.output / 'dataset_validation.json', validation)
    groups = connected_groups(cases)
    rows, excluded = [], []
    for index, case in enumerate(cases):
        if not case['eligible_for_core_metrics'] or case['language_a'] != case['language_b'] or case['language_a'] not in {'java', 'python'}:
            excluded.append({'pair_id': case['pair_id'], 'reason': 'INELIGIBLE_OR_OUTSIDE_SAME_LANGUAGE_SCOPE'})
            continue
        result = analyze_token_pair(_request(index + 1, case, 'PICAS_STANDARD'))
        weights = {m.name: m.weight for m in result.metrics}
        rows.append({'pair_id': case['pair_id'], 'split': case['split'], 'label': case['experiment_label'],
                     'problem_id': case['problem_id'], 'source_id': case['source_id'], 'group_id': groups[case['pair_id']],
                     'language': case['language_a'], 'case_type': case['case_type'], 'problem_type': case['problem_type'],
                     'raw': result.token_similarity, 'ast': result.ast_similarity,
                     'canonical': result.canonical_token_similarity, 'mapping': result.identifier_mapping_similarity,
                     'full': result.weighted_similarity_score, 'dynamic_threshold': result.dynamic_threshold,
                     'fusion_enabled': weights.get('CANONICAL_TOKEN_SIMILARITY', 0) > 0,
                     'warnings': ' | '.join(e.description for e in result.evidence if e.evidence_type == 'PARSER_WARNING')})
    # Connected families may transitively join problems, even without shared hashes.
    splits = defaultdict(set)
    for row in rows:
        splits[row['group_id']].add(row['split'])
    if any(len(value) > 1 for value in splits.values()):
        raise ValueError('Connected-group leakage across validation/test')
    write_csv(args.output / 'scores.csv', rows)
    write_csv(args.output / 'excluded.csv', excluded)
    result = evaluate(rows, config)
    export_evaluation(args.output / 'picas', result)
    label = 'DEVELOPMENT / SYNTHETIC SEED' if args.allow_development else 'FROZEN PROTOCOL / OBSERVED DATA'
    plot_results(args.output / 'picas', result, label)
    baseline_summary = {'status': 'SKIPPED', 'comparable': False}
    if not args.skip_jplag:
        baseline_dir = args.output / 'jplag'
        baseline_dir.mkdir()
        preparation = prepare_inputs(ROOT / config['datasetManifest'], baseline_dir)
        baseline, runs = execute_jplag(baseline_dir, preparation['alignmentRows'], args.jplag_jar.resolve(),
                                      args.java.resolve(), config['jplagVersion'], config['jplagMinTokens'])
        write_csv(baseline_dir / 'baseline_results.csv', baseline)
        write_json(baseline_dir / 'execution.json', runs)
        available = {r['pairId']: r['predictedScore'] for r in baseline if r['resultStatus'] == 'MATCHED'}
        common = [{**r, 'jplag': available[r['pair_id']]} for r in rows if r['pair_id'] in available]
        write_csv(baseline_dir / 'common_scores.csv', common)
        write_csv(baseline_dir / 'unmatched.csv', [{'pair_id': r['pair_id'], 'split': r['split'], 'label': r['label'],
                   'reason': next((b['reason'] for b in baseline if b['pairId'] == r['pair_id']), 'NOT_ALIGNED')} for r in rows if r['pair_id'] not in available])
        baseline_summary = {'status': 'RUN_FAILED' if any(r['exitCode'] != 0 for r in runs) else 'EXECUTED', 'comparable': False, 'requested': len(rows),
                            'matched': len(common), 'missing': len(rows) - len(common),
                            'jarSha256': digest(args.jplag_jar.read_bytes()), 'version': config['jplagVersion'],
                            'minTokens': config['jplagMinTokens'], 'normalization': False, 'templateMode': 'NONE'}
        try:
            comparison = evaluate(common, config, ('FULL_FIXED', 'FULL_DYNAMIC', 'JPLAG_FIXED'))
        except ValueError as error:
            baseline_summary['unavailableReason'] = str(error)
        else:
            # Reselect ALL methods on the same matched validation subset.
            export_evaluation(baseline_dir, comparison)
            plot_results(baseline_dir, comparison, label + ' / JPlag matched subset')
            baseline_summary['comparable'] = True
    code_files = sorted((ROOT / 'analysis-service-python/app').rglob('*.py')) + sorted((ROOT / 'experiment').glob('*.py'))
    code_hashes = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p.read_bytes()) for p in code_files}
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    source_status = subprocess.run(['git', 'status', '--porcelain', '--', 'analysis-service-python', 'experiment', 'configs'], cwd=ROOT, capture_output=True, text=True)
    data_hash = digest(json.dumps(cases, ensure_ascii=False, sort_keys=True).encode('utf-8'))
    run = {'status': 'COMPLETED', 'claimLevel': label, 'startedFromGit': git.stdout.strip(),
           'sourceWorkingTreeDirty': bool(source_status.stdout.strip()), 'sourceSha256': code_hashes,
           'configSha256': digest(config_bytes), 'datasetSha256': data_hash, 'datasetVersion': manifest['dataset_version'],
           'completedAt': datetime.now(timezone.utc).isoformat(), 'python': sys.version, 'platform': platform.platform(),
           'packages': {p: importlib.metadata.version(p) for p in ('pydantic', 'matplotlib', 'numpy')},
           'formalBlockers': blockers, 'baseline': baseline_summary, 'rowCount': len(rows),
           'sourceGroupCount': len(set(groups.values())), 'productionFormulaChanged': False}
    write_json(args.output / 'run_manifest.json', run)
    report = ['# Fair evaluation run', '', f'Claim level: **{label}**', '',
              f"Dataset: {manifest['dataset_version']}; eligible same-language pairs: {len(rows)}.",
              'This run checks the evaluation pipeline. Previously inspected seed data cannot establish generalization.' if args.allow_development else 'Interpret only within the collected dataset and documented sampling limits.', '',
              '## Test metrics', '', '| Method | N | TP | FP | TN | FN | F1 | FPR |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in result['metrics']:
        if row['split'] == 'test':
            fmt = lambda value: 'N/A' if value is None else f'{value:.4f}'
            report.append(f"| {row['method']} | {row['n']} | {row['tp']} | {row['fp']} | {row['tn']} | {row['fn']} | {fmt(row['f1'])} | {fmt(row['fpr'])} |")
    report += ['', 'Selection uses validation F1, lower FPR tie-break, then the documented parameter tie-break.',
               'Ablation removes canonical-token and identifier-mapping signals; remaining weights are .50 raw + .50 AST. All degraded paths retain raw-token fallback.',
               'Cluster percentile intervals condition on selected parameters; they do not include tuning uncertainty. Few independent groups and synthetic data sharply limit interpretation.',
               'Blank CSV metric cells mean undefined denominators. Missing JPlag comparisons are excluded and listed, never imputed as zero.',
               f"JPlag matched coverage: {baseline_summary.get('matched', 0)}/{len(rows)}; comparable: {baseline_summary['comparable']}.",
               'JPlag comparison reselects all thresholds on its common validation subset; inspect jplag/metrics.csv separately from picas/metrics.csv.',
               'Template removal and JPlag normalization are disabled in this protocol; min-tokens is fixed in the configuration, not optimized here.', '',
               '![PICAS test metrics](picas/comparison.png)', '']
    (args.output / 'REPORT.md').write_text('\n'.join(report), encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'rows': len(rows), 'baseline': baseline_summary}, ensure_ascii=False))


if __name__ == '__main__':
    main()
