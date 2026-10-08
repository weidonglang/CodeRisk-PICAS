"""Import a bounded official CodeNet archive prefix and pinned MDN HTML sources. Intake only."""
from __future__ import annotations

import argparse
from collections import Counter
import io
import json
from pathlib import Path
import re
import tarfile
import urllib.request

from acquire_public_datasets import digest, fetch, store, text_digest, verify_intake, write_json, write_rows

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATTERN = re.compile(r'Project_CodeNet/data/(p\d{5})/(C|Java|Python)/(s\d{9})\.(c|java|py)')


def pinned_file(cache: Path, name: str, url: str, sha256: str, offline: bool) -> bytes:
    target = cache / name
    if not target.exists():
        if offline:
            raise FileNotFoundError(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        fetch(url, target)
    data = target.read_bytes()
    if digest(data) != sha256:
        raise ValueError(f'Pinned content changed: {name}')
    return data


def acquire_prefix(cache: Path, config: dict, offline: bool) -> bytes:
    target = cache / config['cache_name']
    expected_size = config['range_end_inclusive'] + 1
    if not target.exists():
        if offline:
            raise FileNotFoundError(target)
        request = urllib.request.Request(config['archive_url'], headers={
            'User-Agent': 'CodeRisk-academic-intake/1.0', 'Range': f'bytes=0-{expected_size - 1}'})
        with urllib.request.urlopen(request, timeout=60) as response:
            expected_range = f'bytes 0-{expected_size - 1}/{config["archive_total_bytes_reported"]}'
            if response.status != 206 or response.headers.get('Content-Range') != expected_range or response.headers.get('ETag') != config['etag']:
                raise ValueError('Server did not return the pinned bounded CodeNet range')
            data = response.read(expected_size + 1)
        if len(data) != expected_size or digest(data) != config['sha256']:
            raise ValueError('CodeNet prefix differs from pin; do not treat it as a complete archive')
        store(target, data)
    data = target.read_bytes()
    if len(data) != expected_size or digest(data) != config['sha256']:
        raise ValueError('CodeNet cached prefix size/hash mismatch')
    return data


def select_codenet(prefix: bytes, output: Path, limit: int) -> tuple[list[dict], dict]:
    if limit < 1:
        raise ValueError('Per-problem language limit must be positive')
    counts = Counter()
    statements, records, excluded = {}, [], []
    end_status = 'COMPLETE_ARCHIVE'
    try:
        with tarfile.open(fileobj=io.BytesIO(prefix), mode='r|gz') as archive:
            for member in archive:
                if not member.isfile():
                    continue
                if member.size > 2 * 1024 * 1024:
                    continue
                statement = re.fullmatch(r'Project_CodeNet/problem_descriptions/(p\d{5})\.html', member.name)
                source = SOURCE_PATTERN.fullmatch(member.name)
                if not statement and not source:
                    continue
                if source and source[4] != {'C': 'c', 'Java': 'java', 'Python': 'py'}[source[2]]:
                    raise ValueError('Source language folder and extension mismatch')
                if source and counts[(source[1], source[2])] >= limit:
                    continue
                # Read each member completely before writing/indexing; never extract the tar paths.
                code = archive.extractfile(member).read()
                if len(code) != member.size:
                    raise ValueError('Incomplete selected tar member')
                if statement:
                    statements[statement[1]] = code
                    continue
                problem, folder, submission, extension = source.groups()
                try:
                    code.decode('utf-8')
                except UnicodeDecodeError:
                    excluded.append({'upstream_path': member.name, 'reason': 'Non-UTF8; retained only in archive prefix, not silently decoded'})
                    continue
                if not code.strip():
                    excluded.append({'upstream_path': member.name, 'reason': 'Empty source'})
                    continue
                language = {'C': 'c', 'Java': 'java', 'Python': 'python'}[folder]
                path = f'sources/{problem}/{language}/{submission}.{extension}'
                records.append({'submission_id': f'CODENET-{submission}', 'upstream_submission_id': submission,
                                'problem_id': 'codenet:' + problem, 'upstream_problem_id': problem,
                                'upstream_archive_member': member.name, 'language': language,
                                'code_path': path, 'code_sha256_bytes': store(output / path, code),
                                'code_sha256_text': text_digest(code), 'encoding': 'utf-8',
                                'published_judge_status': 'UNKNOWN_METADATA_NOT_IN_PREFIX',
                                'author_id_available': False, 'pair_relationship_label': 'UNLABELLED',
                                'eligible_for_core_metrics': False, 'synthetic': False})
                counts[(problem, folder)] += 1
    except (EOFError, tarfile.ReadError):
        # A bounded prefix intentionally ends before gzip EOF. Only fully read prior members are indexed.
        end_status = 'EXPECTED_TRUNCATED_ARCHIVE_PREFIX'
    if not records:
        raise ValueError('No complete CodeNet source files found')
    selected_problems = sorted({r['upstream_problem_id'] for r in records})
    for problem in selected_problems:
        if problem in statements:
            store(output / 'problem_descriptions' / (problem + '.html'), statements[problem])
    for record in records:
        record['problem_description_path'] = ('problem_descriptions/' + record['upstream_problem_id'] + '.html'
                                              if record['upstream_problem_id'] in statements else None)
    write_rows(output / 'submissions.jsonl', records)
    write_json(output / 'exclusions.json', excluded)
    return records, {'archive_read_status': end_status, 'problem_count': len(selected_problems),
                     'language_counts': dict(Counter(r['language'] for r in records)),
                     'selected_source_files': len(records), 'statement_files': len(set(selected_problems) & statements.keys()),
                     'per_problem_language_limit': limit, 'excluded_encoding_or_empty': len(excluded),
                     'published_pair_labels': 0, 'author_grouping_available': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=ROOT / 'data/tools/public-datasets')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify_intake(args.output)))
        return
    if args.output.exists():
        parser.error('Output already exists; use a new immutable directory')
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads(Path(__file__).with_name('multilang_data_sources.json').read_text(encoding='utf-8'))
    prefix = acquire_prefix(args.cache_dir, config['codenet'], args.offline)
    licenses = {}
    for name in ('codenet', 'mdn'):
        entry = config[name]['license_file']
        licenses[name] = pinned_file(args.cache_dir, entry['cache_name'], entry['url'], entry['sha256'], args.offline)
    args.output.mkdir(parents=True)
    try:
        write_json(args.output / 'source_registry.json', config)
        for name, data in licenses.items():
            store(args.output / name / 'upstream' / config[name]['license_file']['cache_name'], data)
        records, codenet_summary = select_codenet(prefix, args.output / 'codenet', config['codenet']['per_problem_language_limit'])
        mdn_records = []
        for entry in config['mdn']['files']:
            path = entry['upstream_path']
            if not path.startswith('html/') or '..' in Path(path).parts or not path.endswith('.html'):
                raise ValueError('Unexpected MDN reference path')
            data = pinned_file(args.cache_dir / 'mdn-html-files', path, entry['download_url'], entry['sha256'], args.offline)
            data.decode('utf-8')
            local = 'sources/' + path
            mdn_records.append({'submission_id': 'MDN-' + digest(path.encode())[:16], 'language': 'html',
                                'upstream_path': path, 'upstream_commit': config['mdn']['commit'],
                                'code_path': local, 'code_sha256_bytes': store(args.output / 'mdn' / local, data),
                                'code_sha256_text': text_digest(data), 'role': 'OFFICIAL_TEACHING_REFERENCE',
                                'pair_relationship_label': 'UNLABELLED', 'eligible_for_core_metrics': False, 'synthetic': False})
        write_rows(args.output / 'mdn/submissions.jsonl', mdn_records)
        inventory = [{'path': path.relative_to(args.output).as_posix(), 'size_bytes': path.stat().st_size,
                      'sha256': digest(path.read_bytes())} for path in sorted(args.output.rglob('*')) if path.is_file()]
        write_json(args.output / 'file_inventory.json', inventory)
        write_json(args.output / 'intake_summary.json', {
            'status': 'INTAKE_COMPLETE_NO_DETECTOR_SCORES', 'schema_version': 'coderisk-multilang-intake-1',
            'codenet': codenet_summary, 'mdn': {'html_files': len(mdn_records), 'published_pair_labels': 0,
                                              'role': 'OFFICIAL_TEACHING_REFERENCE'},
            'language_counts': {**codenet_summary['language_counts'], 'html': len(mdn_records)},
            'inventory_files': len(inventory), 'eligible_for_core_metrics': 0,
            'detector_scores_computed': False, 'downloaded_code_executed': False,
            'note': 'CodeNet prefix is intentionally incomplete; selected members are complete. No judge-status or independence labels are inferred.'})
    except Exception as error:
        write_json(args.output / 'IMPORT_FAILED.json', {'status': 'INCOMPLETE_DO_NOT_USE', 'error': str(error)})
        raise
    print(json.dumps({'output': str(args.output), 'codenet': codenet_summary, 'mdn_html_files': len(mdn_records)}))


if __name__ == '__main__':
    main()
