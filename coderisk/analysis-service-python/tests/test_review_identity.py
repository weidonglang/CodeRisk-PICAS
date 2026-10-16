"""Synthetic review records test identity separation; never actual human annotations."""
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiment'))
from acquire_public_datasets import digest
from prepare_annotation_workbench import merge_reviews
from research_protocol import formal_blockers


def records(tmp_path,types):
    manifest=tmp_path/'manifest.jsonl'
    manifest.write_text(json.dumps({'review_id':'r','source_a':{'code_sha256_bytes':'a'},'source_b':{'code_sha256_bytes':'b'}})+'\n')
    files=[]
    for i,kind in enumerate(types):
        entry={'review_id':'r','label':'INDEPENDENT','basis':'SYNTHETIC_TEST_ONLY','reviewed_at':'2026-10-09T12:00:00+08:00','hash_a':'a','hash_b':'b'}
        value={'manifest_sha256':digest(manifest.read_bytes()),'reviewer_id':f'TEST-{i}','annotations':[entry]}
        if kind is not None:value.update(reviewer_type=kind,reviewer_context='SYNTHETIC_TEST_ONLY')
        file=tmp_path/f'review-{i}.json';file.write_text(json.dumps(value));files.append(file)
    return manifest,files


@pytest.mark.parametrize('types,status,scope,count',[
    (('HUMAN','HUMAN'),'AGREED','DECLARED_HUMAN_PAIR',2),
    (('AI','AI'),'AI_AGREED','AI_INVOLVED',0),
    (('HUMAN','AI'),'AI_AGREED','AI_INVOLVED',1),
    ((None,None),'AGREED','IDENTITY_UNSPECIFIED',0),
])
def test_ai_agreement_cannot_be_counted_as_human_review(tmp_path,types,status,scope,count):
    manifest,files=records(tmp_path,types)
    result=merge_reviews(manifest,*files)[0]
    assert result['status']==status and result['agreement_scope']==scope
    assert result['declared_human_review_count']==count
    assert not result['human_pair_identity_verified'] and not result['eligible_for_core_metrics']


def test_identity_schema_rejects_invalid_type_and_missing_ai_origin(tmp_path):
    manifest,files=records(tmp_path,('AI','AI'))
    value=json.loads(files[0].read_text());value['reviewer_context']=''
    files[0].write_text(json.dumps(value))
    with pytest.raises(ValueError,match='context'):merge_reviews(manifest,*files)
    value['reviewer_context']='test';value['reviewer_type']=[];files[0].write_text(json.dumps(value))
    with pytest.raises(ValueError,match='type'):merge_reviews(manifest,*files)


def test_formal_gate_requires_declared_humans_and_independence_confirmation():
    case={'pair_id':'SYNTHETIC_TEST_ONLY','eligible_for_core_metrics':True,'synthetic':False,'source_type':'public',
          'split_preregistered':True,'source_family_ids':['test'],'provenance':{'license_or_authorization':'test'},'experiment_label':'INDEPENDENT',
          'annotation':{'reviewer_a':'TEST-A','reviewer_b':'TEST-B','label_basis':'test','reviewed_at':'test','functional_evidence':'test',
                        'status':'AGREED','label':'INDEPENDENT','reviewer_a_type':'HUMAN','reviewer_b_type':'HUMAN','independence_confirmed':True}}
    assert formal_blockers([case])==[]
    case['annotation']['reviewer_a_type']='AI'
    assert 'human reviewers' in formal_blockers([case])[0]
    case['annotation']['reviewer_a_type']='HUMAN';case['annotation']['independence_confirmed']=False
    assert 'independence' in formal_blockers([case])[0]
