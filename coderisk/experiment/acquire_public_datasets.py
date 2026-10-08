"""Acquire pinned public corpora and audit intake; never execute downloaded code or score pairs."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile

from research_protocol import connected_groups, propose_split

ROOT = Path(__file__).resolve().parents[1]
MAX_DOWNLOAD = 40 * 1024 * 1024
MAX_MEMBER = 16 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_digest(data: bytes) -> str:
    """Match the experiment loader's UTF-8 universal-newline text hash."""
    text = data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    return digest(text.encode('utf-8'))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def read_member(archive: zipfile.ZipFile, name: str) -> bytes:
    info = archive.getinfo(name)
    if info.file_size > MAX_MEMBER:
        raise ValueError(f'Archive member exceeds intake limit: {name}')
    return archive.read(info)


def csv_rows(archive: zipfile.ZipFile, name: str) -> list[dict]:
    csv.field_size_limit(MAX_MEMBER)
    # newline='' retains embedded CRLF inside quoted code fields.
    return list(csv.DictReader(io.StringIO(read_member(archive, name).decode('utf-8-sig'), newline='')))


def store(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)
    return digest(data)


def fetch(url: str, target: Path, limit: int = MAX_DOWNLOAD) -> None:
    # An interrupted request never replaces a verified cache file.
    temporary = target.with_name(target.name + '.part')
    request = urllib.request.Request(url, headers={'User-Agent': 'CodeRisk-academic-data-intake/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as handle:
        count = 0
        while chunk := response.read(256 * 1024):
            count += len(chunk)
            if count > limit:
                raise ValueError(f'Download exceeds limit: {target.name}')
            handle.write(chunk)
    temporary.replace(target)


def verify_archive(path: Path, source: dict) -> None:
    if path.stat().st_size != source['size_bytes']:
        raise ValueError(f"Size mismatch: {source['id']}")
    data = path.read_bytes()
    if digest(data) != source['sha256'] or hashlib.md5(data).hexdigest() != source['md5']:
        raise ValueError(f"Checksum mismatch: {source['id']}; do not import or update the pin automatically")


def verify_intake(output: Path) -> dict:
    root = output.resolve()
    if (root / 'IMPORT_FAILED.json').exists():
        raise ValueError('Incomplete import must not be used')
    inventory = json.loads((root / 'file_inventory.json').read_text(encoding='utf-8'))
    seen = set()
    for row in inventory:
        path = (root / row['path']).resolve()
        if not path.is_relative_to(root) or path in seen:
            raise ValueError('Unsafe/duplicate inventory path')
        seen.add(path)
        if path.stat().st_size != row['size_bytes'] or digest(path.read_bytes()) != row['sha256']:
            raise ValueError(f"Intake content changed: {row['path']}")
    summary = json.loads((root / 'intake_summary.json').read_text(encoding='utf-8'))
    if summary['status'] != 'INTAKE_COMPLETE_NO_DETECTOR_SCORES' or summary['inventory_files'] != len(inventory):
        raise ValueError('Invalid intake summary')
    return {'verified_files': len(inventory), 'status': summary['status']}


def read_split(archive: zipfile.ZipFile, name: str) -> list[str]:
    rows = list(csv.reader(io.StringIO(read_member(archive, name).decode('utf-8-sig'))))
    if any(len(row) != 1 or not re.fullmatch(r'[0-9a-f]{8}_[0-9a-f]{8}', row[0]) for row in rows):
        raise ValueError(f'Invalid headerless pair split: {name}')
    pairs = [row[0] for row in rows]
    if len(set(pairs)) != len(pairs):
        raise ValueError(f'Duplicate pair split row: {name}')
    return pairs


def import_ad2022(path: Path, output: Path) -> dict:
    submissions, questions, candidates = [], [], []
    terms = {}
    with zipfile.ZipFile(path) as archive:
        for name in ('README.md', 'Licence.txt'):
            store(output / 'upstream' / name, read_member(archive, 'AD2022dataset/' + name))
        for term in ('19_20', '20_21', '21_22'):
            prefix = 'AD2022dataset/' + term
            tasks = csv_rows(archive, prefix + '_task_descriptions.csv')
            solutions = csv_rows(archive, prefix + '_solutions.csv')
            tests = csv_rows(archive, prefix + '_tests.csv')
            for suffix in ('_task_descriptions.csv', '_solutions.csv', '_tests.csv'):
                store(output / 'upstream' / (term + suffix), read_member(archive, prefix + suffix))
            task_ids = {row['id'] for row in tasks}
            if len(task_ids) != len(tasks) or any(row['question_id'] not in task_ids for row in solutions + tests):
                raise ValueError(f'AD2022 question references invalid: {term}')
            for row in tasks:
                questions.append({'question_id': row['id'], 'term': term, 'upstream_fields': row,
                                  'problem_profile_status': 'NOT_REVIEWED',
                                  'related_topic_across_terms_status': 'LINKING_REQUIRED'})
            for index, row in enumerate(solutions, 1):
                qid, student = row['question_id'], row['student_id']
                if not re.fullmatch(r'\d{2}_\d{2}-\d+-\d+-(java|python)', qid) or not re.fullmatch(r'[A-Z0-9]{8}', student):
                    raise ValueError('Unsafe/unexpected AD2022 identifier')
                language = qid.rsplit('-', 1)[1]
                sid = f'AD2022-{term}-{index:04d}'
                relpath = f'sources/{sid}.{ "java" if language == "java" else "py"}'
                code = row['solution'].encode('utf-8')
                if not code.strip():
                    raise ValueError(f'Empty submission: {sid}')
                submissions.append({'submission_id': sid, 'question_id': qid, 'term': term,
                                    'upstream_csv_row': index + 1, 'upstream_student_id': student,
                                    # Conservatively link repeated pseudonyms across semesters.
                                    'source_family_id': f'ad2022:student:{student}',
                                    'language': language, 'code_path': relpath,
                                    'code_sha256_bytes': store(output / relpath, code),
                                    'code_sha256_text': text_digest(code),
                                    'functional_evidence': 'Publisher reports CodeRunner tests passed; not rerun locally'})
            terms[term] = {'solutions': len(solutions), 'question_language_records': len(tasks),
                           'tests': len(tests), 'observed_student_ids': len({r['student_id'] for r in solutions}),
                           'repeated_question_student_rows': len(solutions) - len({(r['question_id'], r['student_id']) for r in solutions})}
    by_question = defaultdict(list)
    for row in submissions:
        by_question[row['question_id']].append(row)
    # Up to six pairs per language/question, chosen by ID only; no detector scores or inferred negative labels.
    for qid, rows in sorted(by_question.items()):
        selected = []
        students = set()
        for row in sorted(rows, key=lambda row: row['submission_id']):
            if row['upstream_student_id'] not in students:
                selected.append(row)
                students.add(row['upstream_student_id'])
            if len(selected) == 4:
                break
        for i, a in enumerate(selected):
            for b in selected[i + 1:]:
                candidates.append({'pair_id': a['submission_id'] + '__' + b['submission_id'],
                                   'question_id': qid, 'submission_a': a['submission_id'], 'submission_b': b['submission_id'],
                                   'source_family_ids': [a['source_family_id'], b['source_family_id']],
                                   'experiment_label': 'UNCERTAIN', 'eligible_for_core_metrics': False,
                                   'annotation_status': 'UNLABELLED', 'selection_basis': 'first four distinct student IDs in CSV-row order per question'})
    write_rows(output / 'submissions.jsonl', submissions)
    write_rows(output / 'questions.jsonl', questions)
    write_rows(output / 'candidate_pairs.jsonl', candidates)
    student_terms = defaultdict(set)
    for row in submissions:
        student_terms[row['upstream_student_id']].add(row['term'])
    return {'solutions': len(submissions), 'language_counts': dict(Counter(r['language'] for r in submissions)),
            'question_language_records': len(questions),
            'exercise_records_across_terms': len({r['question_id'].rsplit('-', 1)[0] for r in questions}),
            'test_records': sum(t['tests'] for t in terms.values()), 'terms': terms,
            'candidate_pairs': len(candidates), 'published_pair_labels': 0,
            'unique_code_byte_hashes': len({r['code_sha256_bytes'] for r in submissions}),
            'pseudonyms_observed_in_multiple_terms': sum(len(values) > 1 for values in student_terms.values()),
            'eligible_for_core_metrics': 0, 'status': 'REAL_COURSEWORK_UNLABELLED_INTAKE'}


def import_conplag(path: Path, output: Path, seed: int) -> tuple[dict, dict]:
    pairs, cases = [], []
    variants = defaultdict(set)
    split_values = {key: defaultdict(set) for key in ('problems', 'submission_ids', 'raw_byte_hashes', 'raw_text_hashes')}
    with zipfile.ZipFile(path) as archive:
        for name in ('README.md', 'versions/labels.csv', 'versions/train_pairs.csv', 'versions/test_pairs.csv'):
            store(output / 'upstream' / name, read_member(archive, name))
        labels = csv_rows(archive, 'versions/labels.csv')
        upstream = {split: read_split(archive, f'versions/{split}_pairs.csv') for split in ('train', 'test')}
        train, test = set(upstream['train']), set(upstream['test'])
        if train & test:
            raise ValueError('Upstream pair splits overlap')
        seen = set()
        for row in labels:
            a, b, problem, verdict = (row[k] for k in ('sub1', 'sub2', 'problem', 'verdict'))
            if any(not re.fullmatch(r'[0-9a-f]{8}', sid) for sid in (a, b)) or a == b or not problem.isdecimal() or verdict not in ('0', '1'):
                raise ValueError('Invalid ConPlag label row')
            pair = '_'.join(sorted((a, b)))
            if pair in seen:
                raise ValueError(f'Duplicate ConPlag pair: {pair}')
            seen.add(pair)
            if pair not in train | test:
                raise ValueError(f'Missing upstream split: {pair}')
            split = 'train' if pair in train else 'test'
            files = {}
            for version in ('version_1', 'version_2'):
                files[version] = []
                for sid in (a, b):
                    name = f'versions/{version}/{pair}/{sid}.java'
                    code = read_member(archive, name)
                    if not code.strip():
                        raise ValueError(f'Empty code: {name}')
                    record = {'submission_id': sid, 'code_path': name,
                              'code_sha256_bytes': store(output / name, code), 'code_sha256_text': text_digest(code)}
                    files[version].append(record)
                    if version == 'version_1':
                        variants[sid].add(record['code_sha256_bytes'])
                        split_values['submission_ids'][sid].add(split)
                        split_values['raw_byte_hashes'][record['code_sha256_bytes']].add(split)
                        split_values['raw_text_hashes'][record['code_sha256_text']].add(split)
            split_values['problems'][problem].add(split)
            pid = 'CONPLAG-' + pair
            raw = files['version_1']
            case = {'pair_id': pid, 'problem_id': 'conplag:problem:' + problem, 'source_id': pid,
                    'source_family_ids': ['conplag:submission:' + sid for sid in (a, b)],
                    'code_a_sha256': raw[0]['code_sha256_text'], 'code_b_sha256': raw[1]['code_sha256_text']}
            cases.append(case)
            pairs.append({**case, 'language': 'java', 'upstream_problem_ordinal': problem,
                          'upstream_split': split, 'published_verdict': int(verdict),
                          'published_verdict_meaning': 'plagiarized' if verdict == '1' else 'non-plagiarized',
                          'annotation_status': 'PUBLISHED_SINGLE_ANNOTATOR_NOT_LOCAL_DOUBLE_REVIEW',
                          'experiment_label': 'UNCERTAIN', 'eligible_for_core_metrics': False,
                          'question_profile_available': False, 'files': files})
        if seen != train | test:
            raise ValueError('Upstream splits contain unknown pairs')
    write_rows(output / 'published_pairs.jsonl', pairs)
    raw_variants = [{'submission_id': sid, 'byte_hashes': sorted(values)} for sid, values in sorted(variants.items()) if len(values) > 1]
    write_json(output / 'raw_submission_variants.json', raw_variants)
    groups = connected_groups(cases)
    proposal_rows = propose_split(cases, seed)
    proposal = {'status': 'REVIEW_REQUIRED_NOT_PREREGISTERED', 'seed': seed,
                'grouping': 'problem ordinal + submission IDs (including byte variants) + universal-newline code hashes',
                'rows': proposal_rows}
    write_json(output / 'split_proposal.json', proposal)
    overlaps = {key: sorted(value for value, splits in values.items() if len(splits) > 1) for key, values in split_values.items()}
    summary = {'published_pairs': len(pairs), 'published_verdict_counts': dict(Counter(str(r['published_verdict']) for r in pairs)),
               'problem_count': len(split_values['problems']), 'unique_submission_ids': len(variants),
               'submission_ids_with_multiple_raw_byte_versions': len(raw_variants),
               'upstream_split_counts': {split: len(values) for split, values in upstream.items()},
               'upstream_split_overlap_counts': {key: len(values) for key, values in overlaps.items()},
               'upstream_split_overlap_ids': overlaps,
               'proposed_group_count': len(set(groups.values())),
               'proposed_split_counts': dict(Counter(row['proposed_split'] for row in proposal_rows)),
               'template_free_is_paired_view_not_extra_samples': True,
               'eligible_for_core_metrics': 0, 'status': 'PUBLISHED_LABELS_EXTERNAL_INTAKE_PENDING_PROTOCOL'}
    return summary, proposal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=ROOT / 'data/tools/public-datasets')
    parser.add_argument('--output', type=Path, required=True, help='New immutable local intake directory')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--verify-only', action='store_true', help='Verify an existing intake against its file inventory')
    parser.add_argument('--seed', type=int, default=20261008)
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify_intake(args.output)))
        return
    if args.output.exists():
        parser.error('Output already exists; choose a new intake directory')
    registry = json.loads(Path(__file__).with_name('public_dataset_sources.json').read_text(encoding='utf-8'))
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    # Verify all input archives before creating output; only selected data members are read.
    for source in registry['sources']:
        archive = args.cache_dir / source['archive_name']
        if not archive.exists():
            if args.offline:
                raise FileNotFoundError(archive)
            fetch(source['download_url'], archive)
        verify_archive(archive, source)
    metadata_source = registry['sources'][1]
    metadata_path = args.cache_dir / metadata_source['metadata_name']
    if not metadata_path.exists():
        if args.offline:
            raise FileNotFoundError(metadata_path)
        fetch(metadata_source['metadata_url'], metadata_path, MAX_MEMBER)
    metadata_bytes = metadata_path.read_bytes()
    metadata = json.loads(metadata_bytes)
    if str(metadata['id']) != '7332790' or metadata['metadata']['license']['id'] != 'cc-by-4.0':
        raise ValueError('Unexpected ConPlag metadata/license')
    published_archive = next(row for row in metadata['files'] if row['key'] == 'conplag.zip')
    if published_archive['checksum'] != 'md5:' + metadata_source['md5'] or published_archive['size'] != metadata_source['size_bytes']:
        raise ValueError('Zenodo metadata checksum/size differs from pin')
    args.output.mkdir(parents=True)
    try:
        write_json(args.output / 'source_registry.json', registry)
        store(args.output / 'conplag-v3/upstream/zenodo-record.json', metadata_bytes)
        ad = import_ad2022(args.cache_dir / 'ad2022.zip', args.output / 'ad2022')
        conplag, _ = import_conplag(args.cache_dir / 'conplag-v3-conplag.zip', args.output / 'conplag-v3', args.seed)
        inventory = [{'path': path.relative_to(args.output).as_posix(), 'size_bytes': path.stat().st_size,
                      'sha256': digest(path.read_bytes())} for path in sorted(args.output.rglob('*')) if path.is_file()]
        write_json(args.output / 'file_inventory.json', inventory)
        write_json(args.output / 'intake_summary.json', {
            'schema_version': 'coderisk-public-intake-1', 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'INTAKE_COMPLETE_NO_DETECTOR_SCORES', 'intake_only_not_research_v4_manifest': True,
            'ad2022': ad, 'conplag_v3': conplag, 'inventory_files': len(inventory),
            'zenodo_metadata_sha256': digest(metadata_bytes),
            'core_metric_eligible_pairs': 0, 'downloaded_code_executed': False, 'detector_scores_computed': False})
    except Exception as error:
        write_json(args.output / 'IMPORT_FAILED.json', {'status': 'INCOMPLETE_DO_NOT_USE', 'error': str(error)})
        raise
    print(json.dumps({'output': str(args.output), 'ad2022_solutions': ad['solutions'],
                      'conplag_pairs': conplag['published_pairs'], 'core_metric_eligible_pairs': 0}))


if __name__ == '__main__':
    main()
