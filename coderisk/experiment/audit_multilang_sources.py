"""Audit parser coverage only; never score pairs, run sources or assign relationship labels."""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys

from acquire_public_datasets import digest, verify_intake, write_json, write_rows

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis-service-python'))
from app.analyzers.token_similarity import parse_ast_nodes, tokenize_code_with_locations
from app.analyzers.canonicalization import canonicalize_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--intake', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--progress', action='store_true')
    args = parser.parse_args()
    integrity = verify_intake(args.intake)
    if args.evidence.exists():
        parser.error('Use a new immutable evidence directory')
    args.evidence.mkdir(parents=True)
    rows, by_language = [], {}
    for dataset in ('codenet', 'mdn'):
        submissions = args.intake / dataset / 'submissions.jsonl'
        shutil.copyfile(submissions, args.evidence / (dataset + '_submissions.jsonl'))
        for line in submissions.read_text(encoding='utf-8').splitlines():
            record = json.loads(line)
            language = record['language']
            raw = (args.intake / dataset / record['code_path']).read_bytes()
            if digest(raw) != record['code_sha256_bytes']:
                raise ValueError('Source differs from inventory')
            code = raw.decode('utf-8')
            if args.progress:
                print(record['submission_id'], language, flush=True)
            ast = parse_ast_nodes(code, language)
            tokens = tokenize_code_with_locations(code, language)
            canonical = canonicalize_code(code, language, tokens)
            cxx_hints = sorted({token.value for token in tokens if token.value in {'::', 'namespace', 'template', 'class'}}) if language == 'c' else []
            row = {'dataset': dataset, 'submission_id': record['submission_id'], 'language': language,
                   'source_sha256': digest(raw), 'syntax_parsed': ast.parsed,
                   'normalization_mode': canonical.mode, 'parser_note': ast.error,
                   'language_quality_status': 'SYNTAX_COMPATIBLE_NOT_COMPILED' if ast.parsed else 'REQUIRES_LANGUAGE_OR_SYNTAX_REVIEW',
                   'cxx_syntax_hints_in_upstream_c_folder': cxx_hints,
                   'pair_score_computed': False, 'eligible_for_core_metrics': False}
            rows.append(row)
            counts = by_language.setdefault(language, Counter())
            counts['sources'] += 1
            counts['syntax_parsed'] += int(ast.parsed)
            counts['syntax_failed'] += int(not ast.parsed)
            counts['cxx_syntax_hints'] += int(bool(cxx_hints))
            counts[canonical.mode] += 1
    for filename in ('source_registry.json', 'file_inventory.json', 'intake_summary.json'):
        shutil.copyfile(args.intake / filename, args.evidence / filename)
    write_rows(args.evidence / 'source_parse_audit.jsonl', rows)
    summary = {'status': 'PARSER_COVERAGE_AUDIT_ONLY', 'integrity': integrity,
               'by_language': by_language, 'source_count': len(rows),
               'runtime': {'python': sys.version.split()[0], **{package: importlib.metadata.version(package)
                           for package in ('tree-sitter', 'tree-sitter-c', 'tree-sitter-html')}},
               'parser_implementations': {'java': 'simplified structural parser', 'python': 'Python 3 ast',
                                          'c': 'tree-sitter-c', 'html': 'tree-sitter-html'},
               'scope': 'Development coverage audit. Not held-out evaluation. No correctness or plagiarism labels inferred.',
               'detector_pair_scores_computed': False, 'downloaded_sources_executed': False,
               'implementation_sha256': {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in (
                   Path(__file__), Path(__file__).with_name('acquire_multilang_dataset.py'),
                   ROOT / 'analysis-service-python/app/analyzers/structured_languages.py',
                   ROOT / 'analysis-service-python/app/analyzers/token_similarity.py',
                   ROOT / 'analysis-service-python/app/analyzers/canonicalization.py')}}
    write_json(args.evidence / 'source_parse_audit_summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
