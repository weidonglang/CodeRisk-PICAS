import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from acquire_public_datasets import digest
from review_public_data import cpp_hints, python_legacy_status, source_bytes, duplicate_groups
from prepare_annotation_workbench import merge_reviews, script_json
from propose_public_splits import components, title_key
from run_published_conplag import pair_scores, calibrate, verify_no_overlap, evaluate, published_metrics
from app.analyzers.token_similarity import analyze_token_pair
from app.schemas.analyze_schema import AnalyzeMockRequest


def test_cpp_hints_ignore_comments_literals_and_c_identifier():
    assert cpp_hints('/* using namespace std; */ int class=1; char *s="std::vector";') == []
    assert 'STD_QUALIFIER' in cpp_hints('std::vector<int> values;')
    assert 'CLASS_DECLARATION' in cpp_hints('class Widget { public: int x; };')


def test_legacy_python_diagnostic_does_not_execute_source():
    assert python_legacy_status('print "old syntax"') in {'LEGACY_GRAMMAR_ACCEPTED_VERSION_REVIEW_REQUIRED', 'LEGACY_GRAMMAR_UNAVAILABLE'}
    assert python_legacy_status('def broken(:') in {'LEGACY_GRAMMAR_NOT_ACCEPTED', 'LEGACY_GRAMMAR_UNAVAILABLE'}


def test_source_loading_rejects_hash_changes_and_escape(tmp_path):
    base = tmp_path / 'intake'
    base.mkdir()
    (base / 'a.java').write_bytes(b'class A {}')
    assert source_bytes(base, 'a.java', digest(b'class A {}'))[1] == b'class A {}'
    with pytest.raises(ValueError, match='hash mismatch'):
        source_bytes(base, 'a.java', 'wrong')
    (tmp_path / 'outside.java').write_bytes(b'class A {}')
    with pytest.raises(ValueError, match='intake member'):
        source_bytes(base, '../outside.java', digest(b'class A {}'))


def test_duplicate_review_keeps_unknown_relationship():
    rows = [{'code_sha256_text': 'h', 'record_id': str(i), 'dataset': 'ad', 'problem_id': f'p{i}'} for i in range(2)]
    group = duplicate_groups(rows)[0]
    assert group['cross_problem'] and not group['relationship_inferred']


def test_split_components_link_transitively_and_ignore_order():
    rows = [{'review_id': 'a', 'keys': ['p1', 'family']}, {'review_id': 'b', 'keys': ['family', 'shared-view-hash']},
            {'review_id': 'c', 'keys': ['shared-view-hash']}, {'review_id': 'd', 'keys': ['p2']}]
    groups = components(rows, lambda r: r['keys'])
    assert groups['a'] == groups['b'] == groups['c'] != groups['d']
    assert groups == components(list(reversed(rows)), lambda r: r['keys'])
    assert title_key('Sum (Java)') == title_key(' SUM [Python] ')


def test_embedded_source_cannot_close_script_block():
    source = '</script><script>alert(1)</script>&\u2028'
    encoded = script_json({'code': source})
    assert '<' not in encoded and '&' not in encoded and '\u2028' not in encoded
    assert json.loads(encoded)['code'] == source


def review_files(tmp_path, label='INDEPENDENT'):
    manifest = tmp_path / 'manifest.jsonl'
    manifest.write_text(json.dumps({'review_id': 'r', 'source_a': {'code_sha256_bytes': 'a'},
                                    'source_b': {'code_sha256_bytes': 'b'}}) + '\n', encoding='utf-8')
    entry = {'review_id': 'r', 'label': label, 'basis': 'independent creation evidence reference',
             'reviewed_at': '2026-10-09T12:00:00+08:00', 'hash_a': 'a', 'hash_b': 'b'}
    files = []
    for reviewer in ('A', 'B'):
        file = tmp_path / (reviewer + '.json')
        file.write_text(json.dumps({'manifest_sha256': digest(manifest.read_bytes()), 'reviewer_id': reviewer,
                                    'annotations': [entry]}), encoding='utf-8')
        files.append(file)
    return manifest, files


def test_double_review_agreement_never_automatically_qualifies(tmp_path):
    manifest, files = review_files(tmp_path)
    row = merge_reviews(manifest, *files)[0]
    assert row['status'] == 'AGREED' and row['final_label'] == 'INDEPENDENT'
    assert not row['eligible_for_core_metrics']
    value = json.loads(files[1].read_text())
    value['annotations'][0]['label'] = 'UNCERTAIN'
    files[1].write_text(json.dumps(value))
    assert merge_reviews(manifest, *files)[0]['status'] == 'DISAGREED'
    value['annotations'][0]['reviewed_at'] = 'not a date'
    files[1].write_text(json.dumps(value))
    assert merge_reviews(manifest, *files)[0]['status'] == 'INCOMPLETE'


def test_merge_rejects_same_reviewer_and_malformed_entries(tmp_path):
    manifest, files = review_files(tmp_path)
    value = json.loads(files[1].read_text())
    value['reviewer_id'] = ' A '
    files[1].write_text(json.dumps(value))
    with pytest.raises(ValueError, match='distinct'):
        merge_reviews(manifest, *files)
    value['annotations'] = {'r': 'bad'}
    files[1].write_text(json.dumps(value))
    with pytest.raises(ValueError, match='list'):
        merge_reviews(manifest, *files)


@pytest.mark.parametrize('left,right', [
    ('class A { int f(int x){return x+1;} }', 'class B { int g(int y){return y+1;} }'),
    ('class A { int x; int f(){int x=1;return x;} }', 'class B { int y; int g(){int y=2;return y;} }'),
    ('// only comments', '/* only comments */'),
    ('class Broken { int f(', 'class B { int f(){return 1;} }'),
])
def test_cached_pilot_scoring_matches_production(left, right):
    request = AnalyzeMockRequest.model_validate({'question': {'id': 1, 'title': 'test'},
        'submissionA': {'id': 1, 'language': 'java', 'code': left},
        'submissionB': {'id': 2, 'language': 'java', 'code': right}, 'config': {'mode': 'PICAS'}})
    production = analyze_token_pair(request)
    pilot = pair_scores(left, right)
    assert pilot['FULL_FIXED'] == production.weighted_similarity_score
    assert pilot['raw'] == production.token_similarity
    assert pilot['canonical'] == production.canonical_token_similarity


def test_published_threshold_selection_never_uses_test_labels_or_scores():
    rows = [{'split': 'validation', 'published_verdict': 1, 'score': .8},
            {'split': 'validation', 'published_verdict': 0, 'score': .3},
            {'split': 'test', 'published_verdict': 1, 'score': .1}]
    first = calibrate(rows, 'score', [.2, .5, .9])
    rows[-1].update(published_verdict=0, score=1)
    assert first == calibrate(rows, 'score', [.2, .5, .9])
    assert first[0] == .5
    with pytest.raises(ValueError):
        calibrate(rows, 'score', [float('nan')])
    assert evaluate([], 'empty', ['score'], {})['status'] == 'INSUFFICIENT_COHORT'
    assert published_metrics([{'published_verdict': 0, 'score': 0}], 'score', .5)['recall'] is None


def test_published_split_checks_template_free_hash_leakage():
    pairs = [{'pair_id': str(i), 'problem_id': f'p{i}', 'source_family_ids': [f'f{i}'],
              'files': {'version_1': [{'code_sha256_text': f'raw{i}'}],
                        'version_2': [{'code_sha256_text': f'free{i}'}]}} for i in range(2)]
    assignments = {'0': {'proposed_split': 'validation'}, '1': {'proposed_split': 'test'}}
    assert not verify_no_overlap(pairs, assignments)['author_isolation_claimed']
    pairs[1]['files']['version_2'][0]['code_sha256_text'] = 'free0'
    with pytest.raises(ValueError, match='overlap'):
        verify_no_overlap(pairs, assignments)
