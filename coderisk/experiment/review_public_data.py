"""Non-destructive public-source quality review. No pair scoring, relabelling or execution."""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys
import warnings

from acquire_public_datasets import digest, text_digest, verify_intake, write_json, write_rows

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis-service-python'))
from app.analyzers.token_similarity import parse_ast_nodes, tokenize_code_with_locations
from app.analyzers.structured_languages import analyze_source


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def source_bytes(base: Path, relative: str, expected_hash: str):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError('Source path must be an existing intake member')
    data = path.read_bytes()
    if digest(data) != expected_hash:
        raise ValueError('Source hash mismatch: ' + relative)
    return path, data


def cpp_hints(code):
    # Use comment/literal-aware tokens; a C identifier named class alone is not evidence.
    values = [t.value for t in tokenize_code_with_locations(code, 'c') if not t.value.startswith(('"', "'"))]
    text = ' '.join(values)
    patterns = {'USING_NAMESPACE': r'\busing\s+namespace\b', 'STD_QUALIFIER': r'\bstd\s*:\s*:',
                'TEMPLATE_DECLARATION': r'\btemplate\s*<', 'CLASS_DECLARATION': r'\bclass\s+\w+\s*[{:]'}
    return [name for name, pattern in patterns.items() if re.search(pattern, text)]


def python_legacy_status(code):
    # This grammar check is a diagnostic hint, not a declared interpreter version or conversion.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            from lib2to3 import pygram, pytree
            from lib2to3.pgen2 import driver
            driver.Driver(pygram.python_grammar, convert=pytree.convert).parse_string(code.rstrip() + '\n')
        return 'LEGACY_GRAMMAR_ACCEPTED_VERSION_REVIEW_REQUIRED'
    except ImportError:
        return 'LEGACY_GRAMMAR_UNAVAILABLE'
    except Exception:
        return 'LEGACY_GRAMMAR_NOT_ACCEPTED'


def inspect_source(code, language):
    parsed = parse_ast_nodes(code, language)
    result = {'syntax_parsed': parsed.parsed, 'parser_note': parsed.error,
              'language_verification': 'SYNTAX_COMPATIBLE_NOT_COMPILED' if parsed.parsed else 'REVIEW_REQUIRED',
              'compiler_or_interpreter_version': 'UNKNOWN', 'normalization_available': None,
              'cpp_syntax_hints': [], 'python_legacy_diagnostic': None}
    if language == 'c':
        source = analyze_source(code, 'c')
        result['normalization_available'] = source.parsed and source.normalization_available
        result['cpp_syntax_hints'] = cpp_hints(code)
        if result['cpp_syntax_hints']:
            result['language_verification'] = 'CPP_HINTS_IN_UPSTREAM_C_REQUIRES_REVIEW'
    elif language == 'html':
        source = analyze_source(code, 'html')
        result['normalization_available'] = source.parsed and source.normalization_available
    elif language == 'python' and not parsed.parsed:
        result['python_legacy_diagnostic'] = python_legacy_status(code)
    elif language == 'java':
        result['language_verification'] = 'MINIMAL_JAVA_STRUCTURE_ONLY_NOT_COMPILED' if parsed.parsed else 'REVIEW_REQUIRED'
    return result


def collect_sources(public: Path, multilang: Path):
    records = []
    def add(dataset, base, row, *, view='original', problem=None, source_id=None, family=None, role='PUBLIC_UNLABELLED_SOURCE'):
        path, data = source_bytes(base, row['code_path'], row['code_sha256_bytes'])
        records.append({'dataset': dataset, 'view': view, 'language': row['language'],
                        'source_id': source_id or row['submission_id'], 'problem_id': problem or row.get('problem_id', row.get('question_id')),
                        'source_family_id': family, 'code_path': path.relative_to(ROOT).as_posix(),
                        'code_sha256_bytes': digest(data), 'code_sha256_text': text_digest(data),
                        'size_bytes': len(data), 'role': role, 'eligible_for_core_metrics': False,
                        'functional_evidence': row.get('functional_evidence', 'UNKNOWN_NOT_EXECUTED'),
                        'published_judge_status': row.get('published_judge_status', 'UNKNOWN'),
                        'source_executed': False})
    for row in jsonl(public / 'ad2022/submissions.jsonl'):
        add('ad2022', public / 'ad2022', row, family=row['source_family_id'], role='REAL_COURSEWORK_UNLABELLED')
    seen = set()
    for pair in jsonl(public / 'conplag-v3/published_pairs.jsonl'):
        for view, files in pair['files'].items():
            for file in files:
                key = (view, pair['problem_id'], file['submission_id'], file['code_sha256_bytes'])
                if key in seen:
                    continue
                seen.add(key)
                add('conplag-v3', public / 'conplag-v3', {**file, 'language': 'java'}, view=view,
                    problem=pair['problem_id'], source_id='CONPLAG-' + file['submission_id'],
                    family='conplag:submission:' + file['submission_id'], role='PUBLISHED_PAIR_SOURCE_NOT_LOCAL_DOUBLE_REVIEWED')
    for row in jsonl(multilang / 'codenet/submissions.jsonl'):
        add('codenet', multilang / 'codenet', row)
    for row in jsonl(multilang / 'mdn/submissions.jsonl'):
        topic = row['upstream_path'].split('/')[1]
        add('mdn', multilang / 'mdn', row, problem='mdn:module:' + topic, role='OFFICIAL_TEACHING_REFERENCE')
    for row in records:
        row['record_id'] = 'SRC-' + digest(json.dumps([row['dataset'], row['view'], row['problem_id'], row['source_id'], row['code_sha256_bytes']]).encode())[:20]
    if len({r['record_id'] for r in records}) != len(records):
        raise ValueError('Source record collision')
    return records


def duplicate_groups(records):
    groups = defaultdict(list)
    for row in records:
        groups[row['code_sha256_text']].append(row)
    return [{'code_sha256_text': key, 'record_count': len(rows), 'records': [r['record_id'] for r in rows],
             'datasets': sorted({r['dataset'] for r in rows}), 'problems': sorted({r['problem_id'] for r in rows}),
             'cross_problem': len({r['problem_id'] for r in rows}) > 1,
             'cross_dataset': len({r['dataset'] for r in rows}) > 1,
             'relationship_inferred': False} for key, rows in sorted(groups.items()) if len(rows) > 1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-intake', type=Path, default=ROOT / 'data/public-datasets/public-intake-20261008')
    parser.add_argument('--multilang-intake', type=Path, default=ROOT / 'data/public-datasets/multilang-intake-20261008')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output directory')
    integrity = {'public': verify_intake(args.public_intake), 'multilang': verify_intake(args.multilang_intake)}
    records = collect_sources(args.public_intake, args.multilang_intake)
    args.output.mkdir(parents=True)
    cache, summary = {}, {}
    try:
        for index, row in enumerate(records):
            key = (row['language'], row['code_sha256_bytes'])
            if key not in cache:
                cache[key] = inspect_source((ROOT / row['code_path']).read_bytes().decode('utf-8'), row['language'])
            row.update(cache[key])
            group = row['dataset'] + ':' + row['view'] + ':' + row['language']
            counts = summary.setdefault(group, Counter())
            counts['source_records'] += 1
            counts['syntax_parsed'] += int(row['syntax_parsed'])
            counts['syntax_failed'] += int(not row['syntax_parsed'])
            counts['cpp_hints'] += int(bool(row['cpp_syntax_hints']))
            if row['python_legacy_diagnostic']:
                counts[row['python_legacy_diagnostic']] += 1
            if (index + 1) % 500 == 0:
                print(f'Reviewed {index + 1}/{len(records)} source records', flush=True)
        duplicates = duplicate_groups(records)
        write_rows(args.output / 'source_quality_registry.jsonl', records)
        write_json(args.output / 'exact_text_duplicate_groups.json', duplicates)
        write_rows(args.output / 'language_or_syntax_review_queue.jsonl', [r for r in records if not r['syntax_parsed'] or r['cpp_syntax_hints']])
        write_json(args.output / 'quality_summary.json', {
            'status': 'QUALITY_REVIEW_NOT_GROUND_TRUTH', 'client_date': '2026-10-09', 'integrity': integrity,
            'source_records': len(records), 'unique_language_byte_contents': len(cache), 'by_corpus_view_language': summary,
            'duplicate_groups': len(duplicates), 'cross_problem_duplicate_groups': sum(r['cross_problem'] for r in duplicates),
            'cross_dataset_duplicate_groups': sum(r['cross_dataset'] for r in duplicates),
            'pair_scores_computed': False, 'code_executed': False, 'relationship_labels_assigned': False,
            'compiler_version_verified': False, 'implementation_sha256': digest(Path(__file__).read_bytes())})
    except Exception as error:
        write_json(args.output / 'REVIEW_FAILED.json', {'error': str(error), 'status': 'INCOMPLETE_DO_NOT_USE'})
        raise
    print(json.dumps({'output': str(args.output), 'source_records': len(records), 'by_corpus_view_language': summary}))


if __name__ == '__main__':
    main()
