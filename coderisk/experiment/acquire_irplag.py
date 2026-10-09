"""Pinned author-published IR-Plag intake. Never run code, score pairs, or invent human reviews."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import urllib.request
import zipfile

from acquire_public_datasets import digest, store, text_digest, write_json, write_rows

ROOT = Path(__file__).resolve().parents[1]
COMMIT = 'f07e95120680b25f78659ed63cd6130fd05b2df8'
REPOSITORY = 'https://github.com/oscarkarnalim/sourcecodeplagiarismdataset'
PAPER = 'https://www.dcs.warwick.ac.uk/~msj/publications/fulltext/karnalim_budi_toba_joy_infed_2019.pdf'
ISSUE = REPOSITORY + '/issues/3'
PINS = {
    'IR-Plag-Dataset.zip': '1b96b320fd05d164b3a7ee17d8cc36992b728d3be099dc7ec39ddb7fae2ec4a4',
    'README.md': 'fdb9688665eaa57e40c1f9e4c81b7c0f219f7281c8f629afddc2abe2347e4cc2',
    'LICENSE': 'c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4',
}
DISPUTED_CASES = {'case-02', 'case-03', 'case-04', 'case-06', 'case-07'}
# Short paraphrases of paper section 3.2, not a redistribution of its task text.
TASKS = ['重复输出问候语', '圆柱面积与体积', 'BMI分类', '英里公里换算表', '整数数字逆序', '十个整数逆序输出', '四阶矩阵主对角线求和']
PATTERN = re.compile(r'IR-Plag-Dataset/(case-0[1-7])/(original|non-plagiarized|plagiarized)/(.+\.java)')


def pinned(cache: Path, name: str, offline: bool) -> bytes:
    file = cache / name
    if not file.exists():
        if offline:
            raise FileNotFoundError(file)
        url = f'https://raw.githubusercontent.com/oscarkarnalim/sourcecodeplagiarismdataset/{COMMIT}/{name}'
        with urllib.request.urlopen(url, timeout=40) as response:
            data = response.read(5_000_001)
        if len(data) > 5_000_000 or digest(data) != PINS[name]:
            raise ValueError('Pinned download hash/size mismatch: ' + name)
        store(file, data)
    data = file.read_bytes()
    if digest(data) != PINS[name]:
        raise ValueError('Pinned cache hash mismatch: ' + name)
    return data


def select_sources(data: bytes, output: Path) -> list[dict]:
    selected = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) > 2000 or sum(i.file_size for i in infos) > 5_000_000:
            raise ValueError('Archive exceeds intake limits')
        seen = set()
        for info in sorted(infos, key=lambda i: i.filename):
            path = PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or chr(92) in info.orig_filename or ':' in info.orig_filename:
                raise ValueError('Unsafe archive path')
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Archive symlink is forbidden')
            if info.filename in seen:
                raise ValueError('Duplicate archive path')
            seen.add(info.filename)
            if info.is_dir():
                continue
            match = PATTERN.fullmatch(info.filename)
            if not match or info.file_size > 2_000_000:
                raise ValueError('Unexpected archive member')
            case, category, suffix = match.groups()
            suffix_parts = PurePosixPath(suffix).parts
            if (category == 'original' and len(suffix_parts) != 1) or (category == 'non-plagiarized' and len(suffix_parts) != 2) or (category == 'plagiarized' and (len(suffix_parts) != 3 or suffix_parts[0] not in {f'L{i}' for i in range(1,7)})):
                raise ValueError('Unexpected category structure')
            raw = archive.read(info)
            raw.decode('utf-8')  # Fail closed: never silently replace undecodable text.
            identity = 'IRP-' + digest(info.filename.encode())[:20]
            relative = f'sources/{case}/{identity}.java'
            store(output / relative, raw)
            disputed = category == 'non-plagiarized' and case in DISPUTED_CASES and suffix_parts[0] in {'13','15'}
            selected.append({'source_id': identity, 'dataset': 'irplag', 'problem_id': 'irplag:' + case,
                'language': 'java', 'category': category, 'published_relative_path': info.filename,
                'code_path': relative, 'code_sha256_bytes': digest(raw), 'code_sha256_text': text_digest(raw),
                'byte_size': len(raw), 'encoding': 'utf-8', 'published_level': suffix_parts[0] if category == 'plagiarized' else None,
                'public_label_disputed': disputed, 'dispute_url': ISSUE if disputed else None,
                'eligible_for_core_metrics': False, 'locally_executed': False, 'local_human_reviews': 0})
    return selected


def build_pairs(sources: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for source in sources:
        grouped[source['problem_id']].append(source)
    pairs = []
    for problem, records in sorted(grouped.items()):
        originals = [r for r in records if r['category'] == 'original']
        if len(originals) != 1:
            raise ValueError('Each task must have exactly one reference original')
        original = originals[0]
        for r in records:
            if r == original:
                continue
            negative = r['category'] == 'non-plagiarized'
            pairs.append({'pair_id': 'IRPAIR-' + digest((original['source_id'] + r['source_id']).encode())[:20],
                'problem_id': problem, 'source_a': original['source_id'], 'source_b': r['source_id'],
                'published_verdict': 0 if negative else 1, 'published_level': r['published_level'],
                'relationship_basis': 'PUBLISHER_INDEPENDENT_CREATION_PROTOCOL' if negative else 'PUBLISHER_INSTRUCTED_DERIVATION',
                'public_label_disputed': r['public_label_disputed'],
                'exploratory_label_allowed': not r['public_label_disputed'],
                'experiment_label': 'UNCERTAIN', 'eligible_for_core_metrics': False,
                'local_human_reviews': 0, 'paper_url': PAPER,
                'natural_similarity_adjudicated': False, 'selection_uses_detector_scores': False,
                'leakage_block': 'irplag-all-tasks-shared-contributors'})
    return pairs


def verify(output: Path) -> dict:
    manifest_path = output / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for name, expected in manifest['registry_sha256'].items():
            if name not in {'source_registry.jsonl','published_pairs.jsonl'} or digest((output/name).read_bytes()) != expected:
                raise ValueError('Registry hash mismatch')
    records = [json.loads(line) for line in (output / 'source_registry.jsonl').read_text(encoding='utf-8').splitlines()]
    for row in records:
        path = (output / row['code_path']).resolve()
        if not path.is_relative_to(output.resolve()) or digest(path.read_bytes()) != row['code_sha256_bytes']:
            raise ValueError('Source path/hash mismatch')
    pairs = [json.loads(line) for line in (output / 'published_pairs.jsonl').read_text(encoding='utf-8').splitlines()]
    if pairs != build_pairs(records):
        raise ValueError('Pair relationship metadata differs from source provenance')
    if any(r['eligible_for_core_metrics'] or r['local_human_reviews'] for r in records + pairs):
        raise ValueError('Intake must not impersonate human review or formal evidence')
    return {'source_files': len(records), 'pairs': len(pairs), 'all_source_hashes_verified': True}


def acquire(cache: Path, output: Path) -> dict:
    archive = pinned(cache, 'IR-Plag-Dataset.zip', False)
    for name in ('README.md', 'LICENSE'):
        pinned(cache, name, False)
    sources = select_sources(archive, output)
    pairs = build_pairs(sources)
    counts = Counter(r['category'] for r in sources)
    if counts != Counter({'original':7, 'non-plagiarized':105, 'plagiarized':355}):
        raise ValueError('Pinned dataset inventory differs from publisher')
    write_rows(output / 'source_registry.jsonl', sources)
    write_rows(output / 'published_pairs.jsonl', pairs)
    manifest = {'dataset': 'irplag', 'source_commit': COMMIT, 'repository_url': REPOSITORY,
        'input_sha256': PINS, 'paper_doi': '10.15388/infedu.2019.15', 'paper_url': PAPER,
        'published_categories': dict(counts), 'files': len(sources), 'unique_byte_hashes': len({r['code_sha256_bytes'] for r in sources}),
        'positive_reference_pairs': 355, 'negative_reference_pairs_published': 105,
        'negative_reference_pairs_uncontested_by_known_issue': 95, 'disputed_pairs_quarantined': 10,
        'formal_eligible_pairs': 0, 'local_human_reviews': 0, 'detector_scored_pairs': 0,
        'license': 'Repository Apache-2.0; paper describes consent for non-profit research and textbook-derived originals. Raw sources are kept local, not redistributed.',
        'correctness': 'Publisher notes minor output errors; compilation claimed by publisher, not rerun locally.',
        'split_policy': 'No validation/test split yet; shared contributors across seven tasks require one conservative global leakage block until independently justified.',
        'tasks': [{'problem_id': f'irplag:case-0{i}', 'summary': title, 'context_source': 'Paper section 3.2; paraphrase only', 'starter_code_provided': False} for i,title in enumerate(TASKS,1)],
        'registry_sha256': {name:digest((output/name).read_bytes()) for name in ('source_registry.jsonl','published_pairs.jsonl')}}
    write_json(output / 'manifest.json', manifest)
    return {**manifest, 'verification': verify(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT.parent/'.tmp/irplag-source')
    parser.add_argument('--output', type=Path, default=ROOT/'data/public-datasets/irplag-20261009')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if not args.verify_only and args.output.exists():
        parser.error('Output already exists; use --verify-only or a fresh directory')
    print(json.dumps(verify(args.output) if args.verify_only else acquire(args.cache,args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
