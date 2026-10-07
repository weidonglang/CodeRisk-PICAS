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

from app.analyzers.normalized_ir import IR_VERSION, compare_normalized_ir  # noqa: E402


FORMULA_VERSION = 'FORMULA_SPEC_V1'
ALGORITHM_VERSION = f'picas-v2-rule-1.0+{IR_VERSION}-experimental'
RANDOM_SEED = 20260621


def run(dataset_path: Path, output_dir: Path, run_id: str) -> dict[str, object]:
    dataset = json.loads(dataset_path.read_text(encoding='utf-8'))
    dataset_root = dataset_path.parent
    rows: list[dict[str, object]] = []
    for case in dataset['cases']:
        java_code = (dataset_root / case['javaPath']).read_text(encoding='utf-8')
        python_code = (dataset_root / case['pythonPath']).read_text(encoding='utf-8')
        comparison = compare_normalized_ir(java_code, 'java', python_code, 'python')
        status = 'COMPARABLE' if comparison.comparable else 'FALLBACK_NO_IR_EVIDENCE'
        expected = case['expectedStatus']
        rows.append({
            'caseId': case['caseId'],
            'status': status,
            'expectedStatus': expected,
            'passed': status == expected and comparison.similarity >= float(case['expectedSimilarityMin']),
            'similarity': comparison.similarity,
            'coverageJava': comparison.left.coverage,
            'coveragePython': comparison.right.coverage,
            'irJava': [node.kind for node in comparison.left.nodes],
            'irPython': [node.kind for node in comparison.right.nodes],
            'warningsJava': comparison.left.warnings,
            'warningsPython': comparison.right.warnings,
            'reason': comparison.reason,
            'notes': case['notes'],
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        'runId': run_id,
        'experiment': 'V4_PHASE1_CROSSLANG_IR',
        'formulaVersion': FORMULA_VERSION,
        'algorithmVersion': ALGORITHM_VERSION,
        'irVersion': IR_VERSION,
        'datasetVersion': dataset['datasetVersion'],
        'randomSeed': RANDOM_SEED,
        'gitCommit': 'not-a-git-worktree',
        'localVersion': _source_hash(),
        'startedAt': datetime.now(timezone.utc).isoformat(),
        'caseCount': len(rows),
        'passedCount': sum(1 for row in rows if row['passed']),
        'productionScoreIntegration': False,
    }
    _write_json(output_dir / 'run_manifest.json', manifest)
    _write_json(output_dir / 'results.json', {'manifest': manifest, 'cases': rows})
    _write_csv(output_dir / 'predictions.csv', rows)
    (output_dir / 'failure_cases.md').write_text(_failure_report(rows), encoding='utf-8')
    (output_dir / 'experiment_report.md').write_text(_experiment_report(manifest, rows), encoding='utf-8')
    _write_json(output_dir.parent / 'latest-crosslang.json', {
        'runId': run_id,
        'artifactPath': str(output_dir.relative_to(ROOT)).replace('\\', '/'),
        'manifest': manifest,
    })
    return {'manifest': manifest, 'cases': rows, 'outputDir': str(output_dir)}


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = ['caseId', 'status', 'expectedStatus', 'passed', 'similarity', 'coverageJava', 'coveragePython', 'reason', 'notes']
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def _source_hash() -> str:
    digest = hashlib.sha256()
    for path in (
        ANALYSIS_ROOT / 'app/analyzers/normalized_ir.py',
        ANALYSIS_ROOT / 'app/analyzers/token_similarity.py',
    ):
        digest.update(path.read_bytes())
    return 'sha256:' + digest.hexdigest()


def _failure_report(rows: list[dict[str, object]]) -> str:
    failures = [row for row in rows if row['status'] != 'COMPARABLE' or not row['passed']]
    lines = [
        '# V4 Phase 1 Cross-language IR Failure Cases',
        '',
        'These cases document prototype boundaries; they are not semantic-equivalence judgments.',
        '',
    ]
    for row in failures:
        lines.extend([
            '## {}'.format(row['caseId']),
            '',
            '- Status: `{}`'.format(row['status']),
            '- Expected: `{}`'.format(row['expectedStatus']),
            '- Similarity: `{}`'.format(row['similarity']),
            '- Reason: {}'.format(row['reason'] or row['notes']),
            '- Fallback: no `CROSSLANG_IR_MATCH` evidence is emitted when parsing or support checks fail.',
            '',
        ])
    return '\n'.join(lines)


def _experiment_report(manifest: dict[str, object], rows: list[dict[str, object]]) -> str:
    lines = [
        '# V4 Phase 1 Experimental Cross-language IR',
        '',
        '- Run: `{}`'.format(manifest['runId']),
        '- Dataset: `{}`'.format(manifest['datasetVersion']),
        '- Algorithm: `{}`'.format(manifest['algorithmVersion']),
        '- Production score integration: `false` (IR metric weight is 0)',
        '',
        '| Case | Status | IR similarity | Java coverage | Python coverage | Passed |',
        '|---|---|---:|---:|---:|---|',
    ]
    for row in rows:
        lines.append('| {} | {} | {:.4f} | {:.4f} | {:.4f} | {} |'.format(
            row['caseId'], row['status'], row['similarity'],
            row['coverageJava'], row['coveragePython'], row['passed'],
        ))
    lines.extend([
        '',
        'The prototype supports only basic Java/Python input, output, assignment, condition, loop, call, return, comparison, and arithmetic operations.',
        'It does not build CFG/DFG, prove semantic equivalence, or participate in the default PICAS_STANDARD score.',
        '',
    ])
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Run the V4 Phase 1 experimental Java-Python IR cases.')
    parser.add_argument(
        '--dataset',
        type=Path,
        default=ROOT / 'experiment/datasets/v4-phase1-crosslang/cases.json',
    )
    parser.add_argument('--run-id', default='PICAS-V4-PHASE1-XL-20260621-R1')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'data/artifacts/experiments')
    args = parser.parse_args()
    result = run(args.dataset.resolve(), (args.output_root / args.run_id).resolve(), args.run_id)
    print(json.dumps(result['manifest'], ensure_ascii=False))
    return 0 if result['manifest']['passedCount'] == result['manifest']['caseCount'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
