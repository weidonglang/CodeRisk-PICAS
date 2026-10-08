"""Synthetic version/template/short-code development probes; no empirical relationship labels."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from acquire_public_datasets import digest, write_json, write_rows

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis-service-python'))
from app.analyzers.token_similarity import analyze_token_pair
from app.schemas.analyze_schema import AnalyzeMockRequest


def cases():
    def case(name, language, left, right, version_a='', version_b='', starter=''):
        return {'case_id': name, 'source_type': 'SYNTHETIC_DEVELOPMENT_FIXTURE', 'experiment_label': 'UNCERTAIN',
                'eligible_for_core_metrics': False, 'independent_creation_verified': False,
                'request': {'question': {'id': 1, 'title': '四则计算器开发案例', 'description': '输入两个数与运算符，按要求输出计算结果。',
                    'starterLanguage': language if starter else '', 'starterCode': starter,
                    'starterSource': 'Synthetic teacher starter fixture; not collected coursework' if starter else ''},
                    'submissionA': {'id': 1, 'language': language, 'languageVersion': version_a, 'code': left},
                    'submissionB': {'id': 2, 'language': language, 'languageVersion': version_b, 'code': right}}}
    python = 'left=float(input())\nright=float(input())\nprint(left+right)'
    java = 'class Main { static double add(double a, double b){ return a+b; } }'
    c = 'double add(double a, double b){ return a+b; }'
    html = '<html><body><form><input name="left"><input name="right"><button>Calculate</button></form></body></html>'
    return [case('short-python-calculator', 'python', python, python, '3.12', '3.12'),
            case('calculator-different-operation', 'python', python, python.replace('left+right', 'left-right')),
            case('python-version-division', 'python', 'left=5\nright=2\nprint(left/right)', 'left=5\nright=2\nprint(left/right)', '2.7', '3.12'),
            case('python-print-version', 'python', 'print 1', 'print(1)', '2.7', '3.12'),
            case('java-version-calculator', 'java', java, java, '8', '17'),
            case('c-version-calculator', 'c', c, c, 'C99', 'C11'),
            case('html-shared-form', 'html', html, html.replace('Calculate', 'Compute'), 'HTML5', 'HTML5', html),
            case('python-shared-input-starter', 'python', python, python.replace('left+right', 'left-right'), '3.12', '3.12',
                 'left=float(input())\nright=float(input())\n# CODERISK_STUDENT_CODE\n')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output directory')
    args.output.mkdir(parents=True)
    rows = []
    for case in cases():
        request = AnalyzeMockRequest.model_validate(case['request'])
        result = analyze_token_pair(request)
        baseline = request.model_copy(deep=True)
        baseline.question.starter_language = baseline.question.starter_code = baseline.question.starter_source = ''
        baseline.submission_a.language_version = baseline.submission_b.language_version = ''
        original = analyze_token_pair(baseline)
        assert (result.weighted_similarity_score, result.dynamic_threshold) == (original.weighted_similarity_score, original.dynamic_threshold)
        review = next(e.metadata for e in result.evidence if e.metadata.get('category') == 'REVIEW_ASSESSMENT')
        assert not review['relationshipDetermined']
        write_json(args.output / (case['case_id'] + '.json'), {'fixture': case, 'result': result.model_dump(by_alias=True),
                   'baseline_score': original.weighted_similarity_score, 'baseline_threshold': original.dynamic_threshold})
        rows.append({'case_id': case['case_id'], 'language': request.submission_a.language, 'score': result.weighted_similarity_score,
                     'threshold': result.dynamic_threshold, 'review_status': review['status'], 'review_reasons': review['reasons'],
                     'baseline_score_and_threshold_preserved': True, 'eligible_for_core_metrics': False})
    write_rows(args.output / 'case_summary.jsonl', rows)
    paths = [Path(__file__), ROOT / 'analysis-service-python/app/analyzers/review_context.py',
             ROOT / 'analysis-service-python/app/analyzers/token_similarity.py']
    write_json(args.output / 'run_manifest.json', {'status': 'SYNTHETIC_CONTEXT_CHECKS_ONLY', 'case_count': len(rows),
        'client_date': '2026-10-09', 'run_at_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version.split()[0],
        'formal_metric_eligible_pairs': 0, 'downloaded_sources_executed': False,
        'implementation_sha256': {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in paths}})
    print(json.dumps({'cases': len(rows), 'baseline_scores_and_thresholds_preserved': True, 'formal_pairs': 0}))


if __name__ == '__main__':
    main()
