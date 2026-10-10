"""Self-authored alpha-renaming contracts and unsupported-binding counterexamples."""
import pytest

from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.token_similarity import tokenize_code_with_locations, analyze_token_pair, _weighted_similarity
from app.schemas.analyze_schema import AnalyzeMockRequest


def canonical(code, language="python"):
    return canonicalize_code(code, language, tokenize_code_with_locations(code, language))


def test_direct_function_keyword_labels_follow_parameter_bindings():
    left = "def combine(first, *, second=1):\n    return first + second\ncombine(first=2, second=3)\n"
    right = "def merge(left, *, right=1):\n    return left + right\nmerge(left=2, right=3)\n"
    a, b = canonical(left), canonical(right)
    assert a.mode == b.mode == "scope-aware-python"
    assert a.tokens == b.tokens
    for name in ("first", "second"):
        items = [item for item in a.identifiers if item["rawName"] == name]
        assert len(items) == 3
        assert len({item["scopedCanonicalName"] for item in items}) == 1


def test_forward_and_nested_keyword_calls_have_structural_callee_bindings():
    a = "def outer(value):\n    return inner(item=value)\ndef inner(item):\n    return item\nouter(value=1)\n"
    b = "def process(number):\n    return helper(element=number)\ndef helper(element):\n    return element\nprocess(number=1)\n"
    assert canonical(a).tokens == canonical(b).tokens


@pytest.mark.parametrize("expression", ["globals()['value']", "locals()['value']", "eval('value')", "vars()", "getattr(obj, 'value')", "ns = globals"])
def test_dynamic_namespace_access_in_any_scope_is_explicitly_unavailable(expression):
    code = "def solve(value):\n    " + expression + "\n    return value\n"
    result = canonical(code)
    assert result.mode == "lexical-fallback"
    assert result.identifiers == []
    assert result.tokens == [item.value for item in tokenize_code_with_locations(code, "python")]
    assert result.reason.startswith("PYTHON_DYNAMIC_NAME_ACCESS_UNSUPPORTED:")


@pytest.mark.parametrize("code,reason", [
    ("def f(value):\n    return value\nalias=f\nalias(value=1)", "PYTHON_INDIRECT_KEYWORD_CALL_UNSUPPORTED"),
    ("obj.method(value=1)", "PYTHON_ATTRIBUTE_KEYWORD_CALL_UNSUPPORTED"),
    ("def f(value, **options):\n    return value\nf(value=1)", "PYTHON_VARIADIC_KEYWORD_CALL_UNSUPPORTED"),
    ("@decorate\ndef f(value):\n    return value\nf(value=1)", "PYTHON_DECORATED_KEYWORD_CALL_UNSUPPORTED"),
    ("def f(value):\n    return value\nf(**options)", "PYTHON_KEYWORD_EXPANSION_UNSUPPORTED"),
    ("def f(value):\n    return value\nf=other\nf(value=1)", "PYTHON_AMBIGUOUS_FUNCTION_BINDING_UNSUPPORTED"),
    ("def f(value):\n    return value\ndef f(other):\n    return other\nf(value=1)", "PYTHON_AMBIGUOUS_FUNCTION_BINDING_UNSUPPORTED"),
    ("def f(value, /):\n    return value\nf(value=1)", "PYTHON_KEYWORD_PARAMETER_UNRESOLVED"),
])
def test_unresolved_keyword_dispatch_does_not_guess_parameter_mapping(code, reason):
    result = canonical(code)
    assert result.mode == "lexical-fallback"
    assert result.identifiers == []
    assert result.reason.startswith(reason + ":")


def test_external_library_keywords_and_members_stay_raw():
    code = "import math\nvalues = (2, 1)\nresult = sorted(values, reverse=True)\nprint(math.sqrt(result[0]))\n"
    result = canonical(code)
    assert result.mode == "scope-aware-python"
    assert all(word in result.tokens for word in ("math", "sqrt", "sorted", "reverse", "print"))
    assert not any(item["rawName"] in {"sqrt", "sorted", "reverse", "print"} for item in result.identifiers)


def test_java_field_reference_before_local_declaration_does_not_capture_future_local():
    a = "class Main { int value = 1; int f() { int first = value; int value = 2; return first + value; } }"
    b = "class Main { int field = 1; int f() { int initial = field; int local = 2; return initial + local; } }"
    result = canonical(a, "java")
    assert result.tokens == canonical(b, "java").tokens
    values = [item for item in result.identifiers if item["rawName"] == "value"]
    assert values[0]["scopedCanonicalName"] == values[1]["scopedCanonicalName"]
    assert values[2]["scopedCanonicalName"] == values[3]["scopedCanonicalName"]
    assert values[0]["scopedCanonicalName"] != values[2]["scopedCanonicalName"]


def test_java_parse_failure_never_manufactures_identifier_evidence():
    code = "class Broken { int f(int value) { return value;"
    result = canonical(code, "java")
    assert result.mode == "lexical-fallback"
    assert result.identifiers == []
    assert result.tokens == [item.value for item in tokenize_code_with_locations(code, "java")]
    assert result.reason.startswith("JAVA_PARSE_UNAVAILABLE:")


def test_unqualified_java_renames_preserve_standard_library_symbols():
    a = "class Main { int sum(int value) { int total = value + 1; System.out.println(total); return total; } }"
    b = "class Main { int add(int number) { int answer = number + 1; System.out.println(answer); return answer; } }"
    result = canonical(a, "java")
    assert result.tokens == canonical(b, "java").tokens
    assert all(word in result.tokens for word in ("System", "out", "println"))


def test_insertion_is_not_a_rename_action_or_invariance_contract():
    base = "def f(value):\n    return value + 1\n"
    modified = "def f(value):\n    unused = 0\n    return value + 1\n"
    assert canonical(base).tokens != canonical(modified).tokens


def test_production_score_is_not_claimed_invariant_when_raw_tokens_change():
    a = "def f(value):\n    total = value + 1\n    return total\n"
    b = "def process(number):\n    answer = number + 1\n    return answer\n"
    request = AnalyzeMockRequest.model_validate({"taskId": 1, "question": {"id": 1, "title": "Rename contract"},
        "submissionA": {"id": 1, "language": "python", "code": a}, "submissionB": {"id": 2, "language": "python", "code": b}})
    result = analyze_token_pair(request)
    assert result.canonical_token_similarity == 1
    assert result.token_similarity < 1
    assert result.weighted_similarity_score < 1
    assert _weighted_similarity(0.2, 0.4, 0.6, 0.8, True, True) == pytest.approx(0.51)
