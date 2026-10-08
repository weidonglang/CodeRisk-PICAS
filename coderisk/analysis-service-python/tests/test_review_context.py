from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.analyzers.token_similarity import analyze_token_pair
from app.analyzers.review_context import exact_spans
from app.schemas.analyze_schema import AnalyzeMockRequest


def request(left, right=None, language='python', **question):
    return AnalyzeMockRequest.model_validate({'question': {'id': 1, 'title': '计算器', 'description': '输入两个数字和运算符，输出四则运算结果。', **question},
        'submissionA': {'id': 1, 'language': language, 'code': left},
        'submissionB': {'id': 2, 'language': language, 'code': left if right is None else right}})


def metadata(result, category):
    return next(e.metadata for e in result.evidence if e.metadata.get('category') == category)


def test_short_calculator_has_high_similarity_but_insufficient_distinguishing_evidence():
    code = 'a=float(input())\nb=float(input())\nprint(a+b)'
    result = analyze_token_pair(request(code))
    assert result.weighted_similarity_score == 1
    review = metadata(result, 'REVIEW_ASSESSMENT')
    assert review['status'] == 'INSUFFICIENT_DISTINGUISHING_EVIDENCE'
    assert not review['relationshipDetermined'] and not review['policyCalibrated']


def test_version_declarations_preserved_without_conversion_or_score_changes():
    req = request('a=5\nb=2\nprint(a/b)')
    original = analyze_token_pair(req)
    req.submission_a.language_version = 'Python 2.7'
    req.submission_b.language_version = 'Python 3.12'
    result = analyze_token_pair(req)
    context = metadata(result, 'LANGUAGE_COMPATIBILITY')
    assert context['submissionA']['declaredVersion'] == 'Python 2.7'
    assert 'DECLARED_PYTHON2_NOT_VALIDATED_BY_PYTHON3_PARSER' in context['submissionA']['limitations']
    assert 'PYTHON_DIVISION_REQUIRES_VERSION_SEMANTICS_REVIEW' in context['submissionA']['limitations']
    assert not context['submissionA']['sourceConverted']
    assert metadata(result, 'REVIEW_ASSESSMENT')['declaredVersionDifference']
    assert result.weighted_similarity_score == original.weighted_similarity_score
    assert result.dynamic_threshold == original.dynamic_threshold


def test_legacy_print_is_a_hint_not_a_confirmed_version():
    result = analyze_token_pair(request('print 1', 'print(1)'))
    context = metadata(result, 'LANGUAGE_COMPATIBILITY')['submissionA']
    assert 'POSSIBLE_PYTHON2_PRINT_STATEMENT' in context['syntaxHints']
    assert context['declaredVersion'] == 'UNKNOWN' and not context['syntaxParsed']
    assert 'PARSER_OR_VERSION_LIMITATIONS' in metadata(result, 'REVIEW_ASSESSMENT')['reasons']
    normal = analyze_token_pair(request('print("print x and raw_input()") # print 1'))
    assert metadata(normal, 'LANGUAGE_COMPATIBILITY')['submissionA']['syntaxHints'] == []


def test_equivalent_declaration_spelling_and_future_python_version():
    req = request('print(1)')
    req.submission_a.language_version = 'Python 3.12'
    req.submission_b.language_version = '3.12'
    assert not metadata(analyze_token_pair(req), 'REVIEW_ASSESSMENT')['declaredVersionDifference']
    req.submission_a.language_version = '3.99'
    assert 'DECLARED_VERSION_NEWER_THAN_PARSER_RUNTIME' in metadata(analyze_token_pair(req), 'LANGUAGE_COMPATIBILITY')['submissionA']['limitations']


def test_registered_template_diagnostic_keeps_original_score_and_source_locations():
    starter = 'left=float(input())\nright=float(input())\n# CODERISK_STUDENT_CODE\n'
    code = 'left=float(input())\nright=float(input())\nanswer=left+right\nprint(answer)'
    req = request(code)
    original = analyze_token_pair(req)
    req.question.starter_language = 'python'
    req.question.starter_code = starter
    req.question.starter_source = 'synthetic teacher starter fixture; not real coursework'
    result = analyze_token_pair(req)
    template = metadata(result, 'SHARED_TEMPLATE_CONTEXT')
    assert template['submissionA']['matchedTemplateTokens'] > 0
    assert template['submissionA']['effectiveTokenCount'] < template['submissionA']['tokenCount']
    assert template['submissionA']['fragments'][0]['startLine'] == 1
    assert template['submissionA']['fragments'][0]['endLine'] == 2
    assert result.weighted_similarity_score == original.weighted_similarity_score
    assert result.dynamic_threshold == original.dynamic_threshold


def test_template_only_sources_have_unknown_residual_similarity():
    code = 'left=float(input())\nright=float(input())\n'
    result = analyze_token_pair(request(code, starterLanguage='python', starterCode=code, starterSource='synthetic fixture'))
    assert metadata(result, 'SHARED_TEMPLATE_CONTEXT')['nonTemplateTokenSetSimilarity'] is None
    assert metadata(result, 'SHARED_TEMPLATE_CONTEXT')['submissionA']['effectiveTokenCount'] == 0
    assert 'NO_NON_TEMPLATE_CONTENT' in metadata(result, 'REVIEW_ASSESSMENT')['reasons']


def test_short_or_wrong_language_template_does_not_mask_code():
    code = 'left=float(input())\nright=float(input())'
    for language, template in [('python', 'print(1)'), ('java', 'class Main { static int add(int x, int y){ return x+y; } }')]:
        result = analyze_token_pair(request(code, starterLanguage=language, starterCode=template, starterSource='fixture'))
        assert metadata(result, 'SHARED_TEMPLATE_CONTEXT')['submissionA']['matchedTemplateTokens'] == 0


@pytest.mark.parametrize('language,code', [
    ('python', 'text="""before\n# CODERISK_STUDENT_CODE\nafter"""\nprint(text.upper())'),
    ('java', 'class Main { String text="""\n/* CODERISK_STUDENT_CODE */\n"""; int value=1; }'),
    ('html', '<html><body><script>\n<!-- CODERISK_STUDENT_CODE -->\nconsole.log(1);</script></body></html>'),
])
def test_hole_marker_inside_literal_or_embedded_script_is_not_split(language, code):
    req = request(code, language=language, starterLanguage=language, starterCode=code, starterSource='synthetic fixture')
    template = metadata(analyze_token_pair(req), 'SHARED_TEMPLATE_CONTEXT')
    assert template['eligibleSegmentCount'] == 1
    assert template['submissionA']['effectiveTokenCount'] == 0


def test_exact_matching_handles_overlap_without_double_counting():
    assert exact_spans(['a', 'a', 'a'], ['a', 'a']) == [(0, 2), (1, 3)]
    code = 'x=x+x+x+x+x+x+x+x+x'
    req = request(code, starterLanguage='python', starterCode='x+x+x+x+x', starterSource='fixture')
    template = metadata(analyze_token_pair(req), 'SHARED_TEMPLATE_CONTEXT')
    assert template['submissionA']['matchedTemplateTokens'] <= template['submissionA']['tokenCount']


def test_same_algorithm_with_different_branches_is_not_semantically_merged():
    left = 'a=float(input())\nb=float(input())\nprint(a+b)'
    right = 'a=float(input())\nb=float(input())\nprint(a-b)'
    result = analyze_token_pair(request(left, right))
    assert result.canonical_token_similarity < 1
    assert metadata(result, 'SHARED_TEMPLATE_CONTEXT')['registered'] is False


def test_html_does_not_use_algorithm_problem_natural_risk():
    code = '<html><body>' + ''.join(f'<div id="section{i}"><p>content {i}</p></div>' for i in range(35)) + '</body></html>'
    result = analyze_token_pair(request(code, language='html'))
    assert 'HEURISTIC_NATURAL_SIMILARITY_RISK' not in metadata(result, 'REVIEW_ASSESSMENT')['reasons']


def test_long_code_is_not_declared_independent_or_confirmed_relation():
    code = '\n'.join(f'v{i} = {i} + {i+1}' for i in range(50))
    result = analyze_token_pair(request(code, title='复杂表达式分析', description='x' * 1600, constraintsText='1 <= n <= 1000'))
    assert metadata(result, 'REVIEW_ASSESSMENT')['status'] != 'INSUFFICIENT_DISTINGUISHING_EVIDENCE'
    assert not metadata(result, 'REVIEW_ASSESSMENT')['relationshipDetermined']


def test_api_requires_template_source_and_bounds_metadata():
    client = TestClient(app)
    value = request('print(1)').model_dump(by_alias=True)
    value['question'].update(starterCode='x=1', starterLanguage='python')
    assert client.post('/internal/analyze/pair', json=value).status_code == 422
    value['question']['starterSource'] = 'fixture'
    value['submissionA']['languageVersion'] = '3.12\nunsafe'
    assert client.post('/internal/analyze/pair', json=value).status_code == 422
