from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / 'analysis-service-python'
sys.path.insert(0, str(ANALYSIS_ROOT))

from app.analyzers.lightweight_summaries import SUMMARY_VERSION  # noqa: E402
from app.analyzers.normalized_ir import IR_VERSION  # noqa: E402
from app.analyzers.token_similarity import analyze_token_pair  # noqa: E402
from app.schemas.analyze_schema import AnalyzeMockRequest  # noqa: E402


FORMULA_VERSION = 'FORMULA_SPEC_V1'
ALGORITHM_VERSION = f'picas-v2-rule-1.0+{IR_VERSION}+{SUMMARY_VERSION}-experimental'
RANDOM_SEED = 20260621


def run(dataset_path: Path, output_dir: Path, run_id: str) -> dict[str, object]:
    dataset = json.loads(dataset_path.read_text(encoding='utf-8'))
    dataset_root = dataset_path.parent
    threshold = float(dataset['reviewThreshold'])
    weights = dataset['experimentalCompositeWeights']
    rows: list[dict[str, object]] = []

    for index, case in enumerate(dataset['cases'], start=1):
        java_code = (dataset_root / case['javaPath']).resolve().read_text(encoding='utf-8')
        python_code = (dataset_root / case['pythonPath']).resolve().read_text(encoding='utf-8')
        result = analyze_token_pair(_request(index, case['caseId'], java_code, python_code))
        metrics = {metric.name: metric.value for metric in result.metrics}
        evidence_types = {item.evidence_type for item in result.evidence}
        ir = metrics.get('CROSSLANG_IR_SIMILARITY', 0.0)
        control = metrics.get('CROSSLANG_CONTROL_SUMMARY_SIMILARITY', 0.0)
        data_flow = metrics.get('CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY', 0.0)
        composite = round(
            (float(weights['ir']) * ir)
            + (float(weights['controlSummary']) * control)
            + (float(weights['dataFlowSummary']) * data_flow),
            6,
        )
        predicted_related = composite >= threshold
        expected = case['expectedRelation']
        parse_fallback = 'CROSSLANG_IR_MATCH' not in evidence_types
        warnings = _warnings(result)
        failure_type = _failure_type(expected, predicted_related, parse_fallback)
        rows.append({
            'caseId': case['caseId'],
            'caseType': case['caseType'],
            'expectedRelation': expected,
            'tokenSimilarity': result.token_similarity,
            'astSimilarity': result.ast_similarity,
            'canonicalTokenSimilarity': result.canonical_token_similarity,
            'irSimilarity': ir,
            'controlSummarySimilarity': control,
            'dataFlowSummarySimilarity': data_flow,
            'experimentalComposite': composite,
            'reviewThreshold': threshold,
            'predictedRelated': predicted_related,
            'parseFallback': parse_fallback,
            'failureType': failure_type,
            'warnings': warnings,
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = _manifest(run_id, dataset, rows, dataset_path)
    _write_json(output_dir / 'run_manifest.json', manifest)
    _write_json(output_dir / 'results.json', {'manifest': manifest, 'cases': rows})
    _write_csv(output_dir / 'metric_comparison.csv', rows)
    _write_csv(output_dir / 'failure_cases.csv', [row for row in rows if row['failureType'] != 'NONE' or row['warnings']])
    (output_dir / 'experiment_report.md').write_text(_report(manifest, rows), encoding='utf-8')
    try:
        artifact_path = str(output_dir.relative_to(ROOT)).replace('\\', '/')
    except ValueError:
        artifact_path = str(output_dir).replace('\\', '/')
    _write_json(output_dir.parent / 'latest-crosslang-phase2.json', {
        'runId': run_id,
        'artifactPath': artifact_path,
        'manifest': manifest,
    })
    return {'manifest': manifest, 'cases': rows, 'outputDir': str(output_dir)}


def _request(index: int, case_id: str, java_code: str, python_code: str) -> AnalyzeMockRequest:
    return AnalyzeMockRequest.model_validate({
        'taskId': 4200 + index,
        'question': {'id': index, 'title': case_id, 'description': 'V4 Phase 2 experimental case'},
        'submissionA': {'id': index * 10 + 1, 'language': 'java', 'code': java_code},
        'submissionB': {'id': index * 10 + 2, 'language': 'python', 'code': python_code},
        'config': {'mode': 'PICAS_CROSSLANG'},
    })


def _warnings(result: object) -> list[str]:
    warnings: set[str] = set()
    for evidence in result.evidence:
        for key in ('warningsA', 'warningsB'):
            value = evidence.metadata.get(key)
            if isinstance(value, list):
                warnings.update(str(item) for item in value if item)
        if evidence.evidence_type == 'PARSER_WARNING':
            warnings.add(evidence.description)
    return sorted(warnings)


def _failure_type(expected: str, predicted_related: bool, parse_fallback: bool) -> str:
    if expected == 'PARSE_FAILURE':
        return 'EXPECTED_PARSE_FALLBACK' if parse_fallback else 'FABRICATED_STRUCTURE_EVIDENCE'
    if expected == 'RELATED' and not predicted_related:
        return 'FALSE_NEGATIVE'
    if expected == 'INDEPENDENT' and predicted_related:
        return 'FALSE_POSITIVE'
    return 'NONE'


def _manifest(
    run_id: str,
    dataset: dict[str, object],
    rows: list[dict[str, object]],
    dataset_path: Path,
) -> dict[str, object]:
    failures = [row for row in rows if row['failureType'] not in {'NONE', 'EXPECTED_PARSE_FALLBACK'}]
    return {
        'runId': run_id,
        'experiment': 'V4_PHASE2_LIGHTWEIGHT_SUMMARIES',
        'formulaVersion': FORMULA_VERSION,
        'algorithmVersion': ALGORITHM_VERSION,
        'irVersion': IR_VERSION,
        'summaryVersion': SUMMARY_VERSION,
        'datasetVersion': dataset['datasetVersion'],
        'datasetSha256': _sha256(dataset_path),
        'randomSeed': RANDOM_SEED,
        'gitCommit': 'not-a-git-worktree',
        'localVersion': _source_hash(),
        'startedAt': datetime.now(timezone.utc).isoformat(),
        'caseCount': len(rows),
        'failureCount': len(failures),
        'parseFallbackCount': sum(row['parseFallback'] for row in rows),
        'unsupportedWarningCount': sum(bool(row['warnings']) for row in rows),
        'productionScoreIntegration': False,
        'testSetModifiedDuringRun': False,
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        'caseId', 'caseType', 'expectedRelation', 'tokenSimilarity', 'astSimilarity',
        'canonicalTokenSimilarity', 'irSimilarity', 'controlSummarySimilarity',
        'dataFlowSummarySimilarity', 'experimentalComposite', 'reviewThreshold',
        'predictedRelated', 'parseFallback', 'failureType', 'warnings',
    ]
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, 'warnings': ' | '.join(row['warnings'])})


def _sha256(path: Path) -> str:
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def _source_hash() -> str:
    digest = hashlib.sha256()
    for path in (
        ANALYSIS_ROOT / 'app/analyzers/normalized_ir.py',
        ANALYSIS_ROOT / 'app/analyzers/lightweight_summaries.py',
        ANALYSIS_ROOT / 'app/analyzers/token_similarity.py',
    ):
        digest.update(path.read_bytes())
    return 'sha256:' + digest.hexdigest()


def _report(manifest: dict[str, object], rows: list[dict[str, object]]) -> str:
    lines = [
        '# V4 Phase 2 Lightweight Structure Summary Experiment',
        '',
        '- Run: `{}`'.format(manifest['runId']),
        '- Dataset: `{}`'.format(manifest['datasetVersion']),
        '- Algorithm: `{}`'.format(manifest['algorithmVersion']),
        '- Production integration: `false`; every new metric has weight `0`.',
        '- This experiment does not construct complete CFG, DFG, PDG, or semantic equivalence proofs.',
        '',
        '| Case | Expected | Raw token | AST | Canonical | IR | Control summary | Data summary | Composite | Failure |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for row in rows:
        lines.append(
            '| {} | {} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {} |'.format(
                row['caseId'], row['expectedRelation'], row['tokenSimilarity'], row['astSimilarity'],
                row['canonicalTokenSimilarity'], row['irSimilarity'], row['controlSummarySimilarity'],
                row['dataFlowSummarySimilarity'], row['experimentalComposite'], row['failureType'],
            )
        )
    lines.extend(['', '## Failure and Boundary Cases', ''])
    boundary_rows = [row for row in rows if row['failureType'] != 'NONE' or row['warnings']]
    for row in boundary_rows:
        lines.extend([
            '### {}'.format(row['caseId']),
            '',
            '- Classification: `{}`'.format(row['failureType']),
            '- Expected relation: `{}`'.format(row['expectedRelation']),
            '- Experimental composite: `{}`'.format(row['experimentalComposite']),
            '- Parser fallback: `{}`'.format(row['parseFallback']),
            '- Warnings: {}'.format(' | '.join(row['warnings']) or 'none'),
            '',
        ])
    lines.extend([
        'The cases are a fixed small prototype matrix, not a benchmark. No threshold or case label was changed during the run.',
        '',
    ])
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run V4 Phase 2 lightweight cross-language summaries.')
    parser.add_argument(
        '--dataset',
        type=Path,
        default=ROOT / 'experiment/datasets/v4-phase2-crosslang/cases.json',
    )
    parser.add_argument('--run-id', default='PICAS-V4-PHASE2-XL-20260621-R1')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'data/artifacts/experiments')
    args = parser.parse_args()
    result = run(args.dataset.resolve(), (args.output_root / args.run_id).resolve(), args.run_id)
    print(json.dumps(result['manifest'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
