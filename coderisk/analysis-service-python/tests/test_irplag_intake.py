"""Synthetic fixtures, not actual research labels."""
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiment'))
from acquire_irplag import acquire, build_pairs, pinned, select_sources, verify
from acquire_public_datasets import digest


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
    with pytest.raises(ValueError,match='manifest is required'):
        verify(tmp_path)


@pytest.fixture
def synthetic_intake(tmp_path, monkeypatch):
    """Full structural inventory, entirely invented test code, never research data."""
    import acquire_irplag
    entries=[]
    for case, derived_count in enumerate([40,54,52,54,53,51,51],1):
        prefix=f'IR-Plag-Dataset/case-0{case}'
        entries.append((prefix+'/original/T.java',f'class Original{case} {{}}\r\n'.encode()))
        for student in range(1,16):
            entries.append((prefix+f'/non-plagiarized/{student:02}/T.java',f'class Independent{case}_{student} {{}}'.encode()))
        for variant in range(1,derived_count+1):
            entries.append((prefix+f'/plagiarized/L1/{variant:02}/T.java',f'class Derived{case}_{variant} {{}}'.encode()))
    cache=tmp_path/'cache'
    cache.mkdir()
    cache_data={'IR-Plag-Dataset.zip':zipped(entries),'README.md':b'SYNTHETIC FIXTURE','LICENSE':b'SYNTHETIC FIXTURE'}
    for name,data in cache_data.items():(cache/name).write_bytes(data)
    monkeypatch.setattr(acquire_irplag,'PINS',{name:digest(data) for name,data in cache_data.items()})
    intake=tmp_path/'intake'
    acquire(cache,intake)
    return intake,cache


def rewrite_registries(intake, records):
    """Tamper even the self-reported checksums to test the independent ZIP anchor."""
    for name,rows in [('source_registry.jsonl',records),('published_pairs.jsonl',build_pairs(records))]:
        (intake/name).write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')
    manifest=json.loads((intake/'manifest.json').read_text(encoding='utf-8'))
    manifest['registry_sha256']={name:digest((intake/name).read_bytes()) for name in ['source_registry.jsonl','published_pairs.jsonl']}
    (intake/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')


@pytest.mark.parametrize('mutation',['dispute','missing','identity','text_hash'])
def test_registry_rewrites_rejected_against_pinned_archive(synthetic_intake,mutation):
    intake,cache=synthetic_intake
    records=[json.loads(line) for line in (intake/'source_registry.jsonl').read_text(encoding='utf-8').splitlines()]
    if mutation=='dispute':
        for row in records:row['public_label_disputed']=False
    elif mutation=='missing':
        records.pop(next(i for i,row in enumerate(records) if row['category']=='non-plagiarized'))
    elif mutation=='identity':
        records[0]['source_id']='IRP-FORGED-ID'
    else:
        records[0]['code_sha256_text']='0'*64
    rewrite_registries(intake,records)
    with pytest.raises(ValueError,match='differs from pinned archive'):
        verify(intake,cache)


def test_source_bytes_and_offline_cache_are_verified(synthetic_intake):
    intake,cache=synthetic_intake
    assert verify(intake,cache)['source_files']==467
    record=json.loads((intake/'source_registry.jsonl').read_text(encoding='utf-8').splitlines()[0])
    source=intake/record['code_path']
    original=source.read_bytes()
    source.write_bytes(b'class Tampered {}')
    with pytest.raises(ValueError,match='Source path/hash mismatch'):
        verify(intake,cache)
    source.write_bytes(original)
    (cache/'LICENSE').unlink()
    with pytest.raises(FileNotFoundError):
        verify(intake,cache)


def test_review_order_orientation_and_fresh_workbench(synthetic_intake,tmp_path,monkeypatch):
    import prepare_irplag_review
    import prepare_annotation_workbench
    intake,cache=synthetic_intake
    monkeypatch.setattr(prepare_irplag_review,'ROOT',tmp_path)
    monkeypatch.setattr(prepare_annotation_workbench,'ROOT',tmp_path)
    previous=intake/'review'
    previous.mkdir()
    (previous/'workbench.html').write_text('PRESERVE OLD WORKBENCH',encoding='utf-8')
    identities=[]
    for version in ['new-review-1','new-review-2']:
        output=tmp_path/(version+'-metadata')
        workbench=intake/version
        assert prepare_irplag_review.prepare(intake,output,workbench,cache)==52
        secrets=[json.loads(line) for line in (output/'publisher_labels_for_adjudicator.jsonl').read_text(encoding='utf-8').splitlines()]
        reviews=[json.loads(line) for line in (workbench/'review_manifest.jsonl').read_text(encoding='utf-8').splitlines()]
        assert {row['reference_side'] for row in secrets}=={'A','B'}
        assert secrets==prepare_annotation_workbench.stable_order(secrets,'pair_id')
        assert any(not row['public_label_disputed'] for row in secrets[-10:])
        for secret,review in zip(secrets,reviews):
            assert secret['review_source_a']==review['source_a']['source_id']
            assert secret['review_source_b']==review['source_b']['source_id']
            assert secret['source_a']==review['source_a' if secret['reference_side']=='A' else 'source_b']['source_id']
        identities.append([row['review_id'] for row in reviews])
        assert 'not guaranteed label-blind' in json.loads((output/'review_preparation.json').read_text(encoding='utf-8'))['note']
    assert identities[0]==identities[1]
    assert (previous/'workbench.html').read_text(encoding='utf-8')=='PRESERVE OLD WORKBENCH'


def test_existing_review_output_rejected_before_any_write(tmp_path):
    from prepare_irplag_review import prepare
    output=tmp_path/'frozen-evidence'
    output.mkdir()
    existing={'sentinel.bin':b'\x00KEEP\xff', 'blind_batch.jsonl':b'{"frozen":true}\r\n',
              'publisher_labels_for_adjudicator.jsonl':b'OLD LABEL METADATA\n'}
    for name,data in existing.items():(output/name).write_bytes(data)
    # The deliberately absent intake also proves rejection precedes verification
    # and any attempt to create or replace local workbench material.
    workbench=tmp_path/'new-workbench'
    with pytest.raises(ValueError,match='fresh output directory'):
        prepare(tmp_path/'absent-intake',output,workbench)
    assert {path.name:path.read_bytes() for path in output.iterdir()}==existing
    assert not workbench.exists()
