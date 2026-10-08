import pytest
from fastapi.testclient import TestClient

from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.token_similarity import analyze_token_pair, parse_ast_nodes, tokenize_code_with_locations
from app.main import create_app
from app.schemas.analyze_schema import AnalyzeMockRequest


def canonical(code, language):
    return canonicalize_code(code, language, tokenize_code_with_locations(code, language))


def payload(language, left, right, config=None):
    return {'question': {'id': 1, 'title': 'Source comparison'},
            'submissionA': {'id': 1, 'language': language, 'code': left},
            'submissionB': {'id': 2, 'language': language, 'code': right}, 'config': config or {}}


def test_c_parser_and_bindings_are_invariant_under_parameter_local_function_rename():
    left = canonical('int sum(int n) { int total = n + 1; return total; }', 'c')
    right = canonical('int add(int count) { int value = count + 1; return value; }', 'c')
    assert left.mode == right.mode == 'scope-aware-c-subset'
    assert left.tokens == right.tokens
    assert {item['kind'] for item in left.identifiers} == {'FUNC', 'PARAM', 'VAR'}


def test_c_loop_variable_does_not_escape_or_overwrite_parameter():
    result = canonical('int f(int x) { for(int x=0;x<2;x++){} return x; }', 'c')
    uses = [item for item in result.identifiers if item['rawName'] == 'x']
    assert uses[0]['scopedCanonicalName'] == uses[-1]['scopedCanonicalName']
    assert uses[1]['scopedCanonicalName'] != uses[-1]['scopedCanonicalName']


def test_c_declarators_bind_in_order_and_keep_struct_members_external_calls():
    code = 'int y; int f() { int x=y, y=2; struct S s; s.value=x; printf("%d", y); return x; }'
    result = canonical(code, 'c')
    uses = [item for item in result.identifiers if item['rawName'] == 'y']
    assert uses[0]['scopedCanonicalName'] == uses[1]['scopedCanonicalName'] != uses[2]['scopedCanonicalName']
    assert 'value' in result.tokens and 'printf' in result.tokens
    assert not any(item['rawName'] in {'value', 'printf', 'S'} for item in result.identifiers)


def test_c_function_pointer_is_a_variable_and_matches_its_call():
    result = canonical('int (*handler)(int); int f(int x) { return handler(x); }', 'c')
    uses = [item for item in result.identifiers if item['rawName'] == 'handler']
    assert len(uses) == 2 and uses[0]['kind'] == uses[1]['kind'] == 'VAR'
    assert uses[0]['scopedCanonicalName'] == uses[1]['scopedCanonicalName']


@pytest.mark.parametrize('code', ['int f( { return 1; }', 'int f(){ /* unclosed'])
def test_c_invalid_syntax_never_produces_canonical_mapping(code):
    assert not parse_ast_nodes(code, 'c').parsed
    assert canonical(code, 'c').mode == 'lexical-fallback'


@pytest.mark.parametrize('code', ['#define INC(x) ((x)+1)\nint f(int x){return INC(x);}',
                                  'typedef int Num; Num f(Num x){return x;}',
                                  'int value; int f(){extern int value; return value;}',
                                  'int f(int (*callback)(int value), int value){return callback(value);}',
                                  'int f(value) int value; {return value;}'])
def test_c_unexpanded_macros_and_typedefs_are_explicit_fallbacks(code):
    assert parse_ast_nodes(code, 'c').parsed
    result = analyze_token_pair(AnalyzeMockRequest.model_validate(payload('c', code, code)))
    assert canonical(code, 'c').mode == 'lexical-fallback'
    assert result.canonical_token_similarity == 0
    assert any(item.evidence_type == 'PARSER_WARNING' and item.metadata.get('normalizationReasonA') for item in result.evidence)


def test_c_unicode_comments_literals_and_crlf_keep_character_columns_and_multiline_ranges():
    code = 'int f(){ /* 注释 */ char *x="http://a/*b*/";\r\n return 1; }'
    tokens = tokenize_code_with_locations(code, 'c')
    assert '/*' not in [t.value for t in tokens]
    assert '"http://a/*b*/"' in [t.value for t in tokens]
    for token in tokens:
        assert code.splitlines()[token.line - 1][token.column:].startswith(token.value)
    assert next(t for t in tokens if t.value == 'return').line == 2


def test_html_attributes_quotes_entities_and_comments_are_canonicalized_without_renaming_values():
    left = canonical('<DIV id="item" class="box"><p>A &amp; B</p><!--c--></DIV>', 'html')
    right = canonical("<div class='box' id='item'><p>A &#38; B</p></div>", 'html')
    assert left.mode == right.mode == 'html-structure-canonical'
    assert left.tokens == right.tokens
    assert left.identifiers == []
    changed = canonical('<div id="other" class="box"><p>A &amp; B</p></div>', 'html')
    assert changed.tokens != left.tokens


def test_html_text_boundaries_raw_script_pre_and_foreign_attributes_are_preserved():
    assert canonical('<p>A <b>B</b></p>', 'html').tokens != canonical('<p>A<b>B</b></p>', 'html').tokens
    for tag in ('script', 'style', 'pre', 'textarea'):
        assert canonical(f'<{tag}> a\n  b </{tag}>', 'html').tokens != canonical(f'<{tag}> a b </{tag}>', 'html').tokens
    assert canonical('<svg viewBox="0 0 1 1"></svg>', 'html').tokens != canonical('<svg viewbox="0 0 1 1"></svg>', 'html').tokens


def test_html_void_elements_and_optional_end_tags_parse_but_broken_markup_falls_back():
    assert parse_ast_nodes('<!doctype html><ul><li>A<li>B</ul><br><input disabled>', 'html').parsed
    assert canonical('<div><span></div>', 'html').mode == 'lexical-fallback'
    assert not parse_ast_nodes('<div title="unclosed>', 'html').parsed
    assert canonical('<div id="a" id="b"></div>', 'html').mode == 'lexical-fallback'


def test_html_line_ranges_cover_multiline_embedded_text_and_unicode_columns():
    code = '<div title="中文">\n<script>\nconst value = 1;\n</script>\n</div>'
    tokens = tokenize_code_with_locations(code, 'html')
    for token in tokens:
        assert code.splitlines()[token.line - 1][token.column:].startswith(token.value.splitlines()[0])
        assert token.line <= token.end_line <= 5
    raw = next(t for t in tokens if 'const value' in t.value)
    assert raw.line <= 3 <= raw.end_line


@pytest.mark.parametrize('language,code', [('c', 'int f(int x){return x+1;}'),
                                         ('html', '<div id="a"><p>Hello</p></div>')])
def test_api_returns_real_new_language_scores_with_correct_parser_and_evidence(language, code):
    with TestClient(create_app()) as client:
        response = client.post('/internal/analyze/pair', json=payload(language, code, code))
        assert response.status_code == 200
        result = response.json()['result']
        assert result['isMock'] is False and result['weightedSimilarityScore'] == 1.0
        assert any(item['metadata'].get('parser') == 'tree-sitter-' + language for item in result['evidence'])
        assert result['evidence'][0]['metadata']['fragments']
        if language == 'html':
            assert result['formulaVersion'] == 'HTML_STRUCTURE_FIXED_V1'
            assert result['thresholdAdjustment']['policy'] == 'FIXED_UNCALIBRATED'
            assert result['dynamicThreshold'] == 0.85
            assert result['problemProfile']['domain'] == 'html'
            assert sum(metric['weight'] for metric in result['metrics']) == 1.0


@pytest.mark.parametrize('language,code', [('html', '<!--only-->'), ('c', '/*only*/'), ('python', '#only')])
def test_comment_only_sources_never_receive_a_perfect_score(language, code):
    result = analyze_token_pair(AnalyzeMockRequest.model_validate(payload(language, code, code)))
    assert result.weighted_similarity_score == result.token_similarity == result.ast_similarity == 0.0


def test_api_rejects_mixed_html_c_domains_and_nonfinite_html_threshold():
    with TestClient(create_app()) as client:
        mixed = payload('html', '<div>x</div>', 'int main(){return 0;}')
        mixed['submissionB']['language'] = 'c'
        assert client.post('/internal/analyze/pair', json=mixed).status_code == 400
        invalid = payload('html', '<br>', '<br>', {'htmlThreshold': 'NaN'})
        assert client.post('/internal/analyze/pair', json=invalid).status_code == 400


@pytest.mark.parametrize('value', [None, {}, []])
def test_html_invalid_threshold_types_are_client_errors(value):
    with TestClient(create_app()) as client:
        assert client.post('/internal/analyze/pair', json=payload('html', '<br>', '<br>', {'htmlThreshold': value})).status_code == 400


def test_html_does_not_build_unused_algorithm_problem_thresholds():
    with TestClient(create_app()) as client:
        response = client.post('/internal/analyze/pair', json=payload('html', '<br>', '<br>', {'baseThreshold': 'not-an-algorithm-threshold'}))
        assert response.status_code == 200
        assert response.json()['result']['dynamicThreshold'] == 0.85
