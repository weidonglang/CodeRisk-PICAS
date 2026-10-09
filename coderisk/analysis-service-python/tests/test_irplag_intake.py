"""Synthetic fixtures, not actual research labels."""
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiment'))
from acquire_irplag import build_pairs, pinned, select_sources, verify


def zipped(entries):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as archive:
        for name,data in entries:
            archive.writestr(name,data)
    return buffer.getvalue()


def test_author_labels_and_disputed_negatives_stay_separate(tmp_path):
    rows=select_sources(zipped([
        ('IR-Plag-Dataset/case-02/original/T.java',b'class Main { }\r\n'),
        ('IR-Plag-Dataset/case-02/non-plagiarized/13/T.java',b'class Independent { }'),
        ('IR-Plag-Dataset/case-02/non-plagiarized/01/T.java',b'class Other { }'),
        ('IR-Plag-Dataset/case-02/plagiarized/L2/01/T.java',b'class Renamed { }'),
    ]),tmp_path)
    pairs=build_pairs(rows)
    assert len(pairs)==3
    disputed=next(p for p in pairs if p['public_label_disputed'])
    assert disputed['published_verdict']==0 and not disputed['exploratory_label_allowed']
    assert all(p['experiment_label']=='UNCERTAIN' and not p['eligible_for_core_metrics'] for p in pairs)
    assert all(p['local_human_reviews']==0 for p in pairs)
    assert {p['leakage_block'] for p in pairs}=={'irplag-all-tasks-shared-contributors'}
    original=next(r for r in rows if r['category']=='original')
    assert (tmp_path/original['code_path']).read_bytes().endswith(b'\r\n')


@pytest.mark.parametrize('name',['../escape.java','/escape.java','C:/escape.java','a\\b.java'])
def test_unsafe_archive_paths_rejected(tmp_path,name):
    # Windows ZipInfo normalizes backslashes while writing. Change both ZIP filename
    # headers after writing to exercise a genuinely supplied backslash path.
    raw=zipped([(name.replace(chr(92),'/'),b'class A{}')])
    if chr(92) in name:
        raw=raw.replace(name.replace(chr(92),'/').encode(),name.encode())
    with pytest.raises(ValueError,match='Unsafe archive path'):
        select_sources(raw,tmp_path)


def test_pin_and_source_hash_tampering_rejected(tmp_path):
    (tmp_path/'LICENSE').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='hash mismatch'):
        pinned(tmp_path,'LICENSE',True)
    (tmp_path/'code.java').write_bytes(b'changed')
    (tmp_path/'source_registry.jsonl').write_text(json.dumps({'code_path':'code.java','code_sha256_bytes':'0'*64})+'\n')
    with pytest.raises(ValueError,match='hash mismatch'):
        verify(tmp_path)
