import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from group_action_oracle import BOUNDARIES
from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.token_similarity import tokenize_code_with_locations
from test_health_and_mock import build_client, _pair_payload


@pytest.mark.parametrize('case', [c for c in BOUNDARIES if c[3] != 'ORACLE_UNCERTAIN'], ids=lambda c: c[0])
def test_located_explicit_fallback(case):
    _, language, code, _, reason = case
    tokens = tokenize_code_with_locations(code, language)
    result = canonicalize_code(code, language, tokens)
    assert result.mode == 'lexical-fallback'
    assert result.identifiers == []
    assert result.tokens == [t.value for t in tokens]
    assert result.reason.startswith(reason + ':') and 'line' in result.reason


def test_java_header_shadow_warning_uses_existing_api(tmp_path):
    code = next(c[2] for c in BOUNDARIES if c[0] == 'for-shadow-field')
    client = build_client(tmp_path)
    a, b = tmp_path / 'uploads/a.java', tmp_path / 'uploads/b.java'
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text(code, encoding='utf-8')
    b.write_text('class Main { int fold(int number) { return number; } }', encoding='utf-8')
    response = client.post('/internal/analyze/pair', json=_pair_payload(a, b, 'java'))
    assert response.status_code == 200
    result = response.json()['result']
    assert result['weightedSimilarityScore'] == result['tokenSimilarity']
    evidence = result['evidence']
    warning = next(e for e in evidence if e['evidenceType'] == 'PARSER_WARNING')
    assert warning['metadata']['normalizationReasonA'].startswith('JAVA_HEADER_SHADOW_BINDING_UNSUPPORTED:')
    assert not {'CANONICAL_TOKEN_MATCH', 'IDENTIFIER_MAPPING'} & {e['evidenceType'] for e in evidence}


@pytest.mark.parametrize('code', [
    'class Main { int value; int f(int[] values) { for(int value : values) {} return value; } }',
    'class Main { int value; int f() { try {} catch(Exception value) {} return value; } }',
])
def test_enhanced_for_and_catch_field_shadow_are_also_declined(code):
    result = canonicalize_code(code, 'java', tokenize_code_with_locations(code, 'java'))
    assert result.reason.startswith('JAVA_HEADER_SHADOW_BINDING_UNSUPPORTED:')
    assert result.identifiers == []
