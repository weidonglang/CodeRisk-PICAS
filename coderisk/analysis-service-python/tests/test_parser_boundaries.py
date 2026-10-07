import pytest

from app.analyzers.canonicalization import build_identifier_mapping, canonicalize_code
from app.analyzers.token_similarity import (
    _ast_fingerprint_locations, _fingerprint_locations, parse_ast_nodes, tokenize_code_with_locations,
)


def canonical(code, language="java"):
    return canonicalize_code(code, language, tokenize_code_with_locations(code, language))


def test_java_comments_preserve_original_line_and_column():
    code = 'class A { // comment\r\n  /* a\r\n b */ int count;\r\n}'
    tokens = tokenize_code_with_locations(code, "java")
    count = next(t for t in tokens if t.value == "count")
    assert (count.line, count.column) == (3, code.splitlines()[2].index("count"))
    for token in tokens:
        assert code.splitlines()[token.line - 1][token.column:].startswith(token.value)


@pytest.mark.parametrize("literal", ['"("', "'}'", '"http://host/*path*/"', '\'"\''])
def test_java_literals_do_not_break_delimiter_check(literal):
    code = f'class A {{ Object value = {literal}; }}'
    assert parse_ast_nodes(code, "java").parsed
    assert canonical(code).mode == "scope-aware-java"


def test_java_text_block_is_one_token_and_unclosed_comment_warns():
    code = 'class A { String text = """\n// ( /* \"\n"""; int count; }'
    tokens = tokenize_code_with_locations(code, "java")
    assert sum(t.value.startswith('"""') for t in tokens) == 1
    assert parse_ast_nodes(code, "java").parsed
    assert not parse_ast_nodes('class A {} /* unfinished', "java").parsed


def test_java_invocation_does_not_declare_function_in_method_scope():
    code = 'class A { boolean ok(int x) { return true; } int run(int n) { if (ok(n)) { return n; } return n; } }'
    result = canonical(code)
    ok_scopes = {x["scopePath"] for x in result.identifiers if x["rawName"] == "ok"}
    assert len(ok_scopes) == 1
    assert all(x["kind"] == "PARAM" for x in result.identifiers if x["rawName"] == "n")


def test_java_this_field_is_separate_from_shadowing_parameter_and_external_member():
    code = 'class A { int value; int run(int value) { this.value = value; return other.value; } }'
    result = canonical(code)
    fields = [x for x in result.identifiers if x["rawName"] == "value" and x["kind"] == "VAR"]
    assert len(fields) == 2
    assert fields[0]["scopedCanonicalName"] == fields[1]["scopedCanonicalName"]
    external = code.index("value", code.index("other."))
    assert not any(x["column"] == external for x in result.identifiers)


def test_mapping_display_limit_never_changes_similarity():
    left = canonical("\n".join(f"v{i} = {i}" for i in range(30)), "python")
    right = canonical("\n".join(f"x{i} = {i}" for i in range(30)), "python")
    for limit in (0, 3, 20, 100):
        result = build_identifier_mapping(left, right, limit=limit)
        assert result.similarity == 1.0
        assert len(result.mappings) == min(limit, 30)


def test_python_unicode_columns_bind_every_identifier_occurrence():
    code = 'def 求和(数值):\n    总数 = 数值 + 1\n    return 总数\n'
    result = canonical(code, "python")
    assert len(result.identifiers) == 5
    for item in result.identifiers:
        assert code.splitlines()[item["line"] - 1][item["column"]:].startswith(item["rawName"])


def test_ast_evidence_ranges_cover_all_nodes_in_window():
    parsed = parse_ast_nodes('def f(x):\n    y = x + 1\n    return y\n', "python")
    assert all(n.line >= 2 for n in parsed.nodes if n.value in {"Load", "Store", "Add"})
    locations = _ast_fingerprint_locations(parsed.nodes)
    for start, end in locations.values():
        assert 1 <= start <= end <= 3


@pytest.mark.parametrize('language,code', [('python', 'text = """first\nsecond\nthird"""'),
                                         ('java', 'String text = """\nsecond\nthird\n""";')])
def test_multiline_literal_evidence_includes_closing_line(language, code):
    tokens = tokenize_code_with_locations(code, language)
    locations = _fingerprint_locations(tokens)
    literal = next(t for t in tokens if t.value.startswith('"""'))
    assert literal.end_line == len(code.splitlines())
    assert all(end == literal.end_line for window, (_, end) in locations.items() if window[-1] == literal.value)


def test_scope_fallback_weights_and_warning_match_actual_score(monkeypatch):
    from app.analyzers import token_similarity as analyzer
    from app.analyzers.canonicalization import CanonicalAnalysis
    from app.schemas.analyze_schema import AnalyzeMockRequest
    monkeypatch.setattr(analyzer, 'canonicalize_code', lambda *args: CanonicalAnalysis([], [], 'lexical-fallback'))
    request = AnalyzeMockRequest.model_validate({
        'taskId': 1, 'question': {'id': 1, 'title': 'Test', 'description': 'Return an integer'},
        'submissionA': {'id': 1, 'language': 'python', 'code': 'x = 1'},
        'submissionB': {'id': 2, 'language': 'python', 'code': 'y = 2'},
    })
    result = analyzer.analyze_token_pair(request)
    assert result.weighted_similarity_score == result.token_similarity
    assert sum(m.weight for m in result.metrics) == 1
    assert next(m.weight for m in result.metrics if m.name == 'TOKEN_SIMILARITY') == 1
    assert any(e.evidence_type == 'PARSER_WARNING' for e in result.evidence)
