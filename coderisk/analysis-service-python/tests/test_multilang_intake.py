"""Artificial archive fixtures exercise intake contracts; these are not research data."""
import gzip
import io
from pathlib import Path
import sys
import tarfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from acquire_multilang_dataset import pinned_file, select_codenet


def archive_bytes(entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        for name, data in entries:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return buffer.getvalue()


def test_bounded_tar_keeps_complete_member_only_and_never_infers_labels(tmp_path):
    raw = archive_bytes([
        ('Project_CodeNet/data/p00001/C/s000000001.c', b'int main(){return 0;}'),
        ('Project_CodeNet/data/p00001/C/s000000002.c', b'int f(){return 2;}' * 100),
    ])
    # First header/body blocks complete; second body is intentionally cut short.
    records, summary = select_codenet(gzip.compress(raw[:1600]), tmp_path, 12)
    assert len(records) == 1 and summary['archive_read_status'] == 'EXPECTED_TRUNCATED_ARCHIVE_PREFIX'
    assert records[0]['pair_relationship_label'] == 'UNLABELLED'
    assert not records[0]['author_id_available'] and not records[0]['eligible_for_core_metrics']
    assert list((tmp_path / 'sources/p00001/c').iterdir()) == [tmp_path / records[0]['code_path']]


def test_language_folder_extension_mismatch_is_rejected(tmp_path):
    raw = archive_bytes([('Project_CodeNet/data/p00001/C/s000000001.java', b'class A{}')])
    with pytest.raises(ValueError, match='extension mismatch'):
        select_codenet(gzip.compress(raw), tmp_path, 12)


def test_archive_path_traversal_is_not_extracted(tmp_path):
    raw = archive_bytes([
        ('../../escape.c', b'unsafe'),
        ('Project_CodeNet/data/p00001/C/s000000001.c', b'int main(){return 0;}'),
    ])
    records, summary = select_codenet(gzip.compress(raw), tmp_path, 1)
    assert summary['selected_source_files'] == len(records) == 1
    assert not (tmp_path.parent / 'escape.c').exists()


def test_pinned_cache_change_rejected_without_network(tmp_path):
    (tmp_path / 'sample.html').write_bytes(b'changed')
    with pytest.raises(ValueError, match='Pinned content changed'):
        pinned_file(tmp_path, 'sample.html', 'https://example.invalid/', '0' * 64, True)
