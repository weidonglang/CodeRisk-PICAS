"""Self-authored boundary fixtures; these are not empirical dataset labels."""
import pytest

from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.token_similarity import tokenize_code_with_locations


def canonical(code: str):
    return canonicalize_code(code, "python", tokenize_code_with_locations(code, "python"))


def occurrence(result, name: str, line: int, column: int):
    return next(item for item in result.identifiers
                if (item["rawName"], item["line"], item["column"]) == (name, line, column))


def test_lambda_defaults_and_variadic_parameters_preserve_renaming():
    left = "outer = 1\nf = lambda outer=outer, *items, **options: (outer, items, options)\n"
    right = "base = 1\ng = lambda local=base, *values, **keywords: (local, values, keywords)\n"
    result = canonical(left)
    assert result.tokens == canonical(right).tokens
    assert result.mode == "scope-aware-python"
    assert result.reason is None
    default = occurrence(result, "outer", 2, left.splitlines()[1].index("=outer") + 1)
    assert default["scopedCanonicalName"] == "MODULE::VAR_1"
    for name in ("outer", "items", "options"):
        argument_and_body = [item for item in result.identifiers
                             if item["rawName"] == name and item["kind"] == "PARAM"]
        assert len(argument_and_body) == 2
        assert argument_and_body[0]["scopedCanonicalName"] == argument_and_body[1]["scopedCanonicalName"]


def test_lambda_keyword_defaults_and_positional_only_parameters():
    left = "seed = 4\nf = lambda first, /, *, second=seed: first + second\n"
    right = "base = 4\ng = lambda item, /, *, other=base: item + other\n"
    result = canonical(left)
    assert result.tokens == canonical(right).tokens
    default = next(item for item in result.identifiers if item["rawName"] == "seed" and item["line"] == 2)
    assert default["scopePath"] == "MODULE"


def test_method_body_skips_class_but_default_uses_class_binding():
    code = ("value = 1\nclass A:\n    value = 2\n"
            "    def f(self, item=value):\n        return value + item\n")
    result = canonical(code)
    default = next(item for item in result.identifiers if item["rawName"] == "value" and item["line"] == 4)
    body = next(item for item in result.identifiers if item["rawName"] == "value" and item["line"] == 5)
    assert default["scopedCanonicalName"] == "MODULE/CLASS_1_1::VAR_1"
    assert body["scopedCanonicalName"] == "MODULE::VAR_1"
    renamed = ("outer = 1\nclass B:\n    inner = 2\n"
               "    def g(this, element=inner):\n        return outer + element\n")
    assert result.tokens == canonical(renamed).tokens


def test_class_lambda_default_and_body_use_distinct_scopes():
    code = "value = 1\nclass A:\n    value = 2\n    f = lambda item=value: value + item\n"
    result = canonical(code)
    values = [item for item in result.identifiers if item["rawName"] == "value" and item["line"] == 4]
    assert [item["scopePath"] for item in values] == ["MODULE/CLASS_1_1", "MODULE"]


def test_class_method_can_close_over_enclosing_function_without_class_capture():
    code = ("def outer(value):\n    class A:\n        value = 2\n"
            "        def f(self):\n            def inner():\n                return value\n"
            "            return inner()\n    return A\n")
    result = canonical(code)
    reference = next(item for item in result.identifiers if item["rawName"] == "value" and item["line"] == 6)
    assert reference["scopePath"] == "MODULE/FUNC_1_1"
    assert reference["kind"] == "PARAM"


def test_nested_class_body_skips_outer_class_namespace():
    code = ("value = 1\nclass A:\n    value = 2\n    class B:\n"
            "        copied = value\n        def f(self):\n            return value\n")
    result = canonical(code)
    assert result.mode == "scope-aware-python"
    references = [item for item in result.identifiers
                  if item["rawName"] == "value" and item["line"] in (5, 7)]
    assert len(references) == 2
    assert all(item["scopePath"] == "MODULE" for item in references)


def test_class_method_runtime_branches_do_not_force_class_binding_fallback():
    code = "class A:\n    def f(self, value):\n        if value:\n            return value\n        return 0\n"
    assert canonical(code).mode == "scope-aware-python"


@pytest.mark.parametrize("code,category", [
    ("value = 1\nclass A:\n    value = value + 1", "PYTHON_CLASS_FORWARD_BINDING_UNSUPPORTED"),
    ("value = 1\nclass A:\n    def f(self, item=value):\n        return item\n    value = 2", "PYTHON_CLASS_FORWARD_BINDING_UNSUPPORTED"),
    ("value = 1\nclass A:\n    item = value\n    value = 2", "PYTHON_CLASS_FORWARD_BINDING_UNSUPPORTED"),
    ("value = 1\nclass A:\n    if flag:\n        value = 2\n    item = value", "PYTHON_CLASS_DYNAMIC_BINDING_UNSUPPORTED"),
    ("class A:\n    for value in range(3):\n        pass", "PYTHON_CLASS_DYNAMIC_BINDING_UNSUPPORTED"),
    ("class A:\n    value = 1\n    del value", "PYTHON_CLASS_DYNAMIC_BINDING_UNSUPPORTED"),
    ("class A:\n    value = 1\n    value += 1", "PYTHON_CLASS_DYNAMIC_BINDING_UNSUPPORTED"),
    ("class A:\n    exec('value = 1')", "PYTHON_CLASS_NAMESPACE_UNSUPPORTED"),
    ("class A:\n    locals()['value'] = 1", "PYTHON_CLASS_NAMESPACE_UNSUPPORTED"),
    ("class A:\n    item = eval('value')", "PYTHON_CLASS_NAMESPACE_UNSUPPORTED"),
    ("class A(metaclass=Factory):\n    value = 1", "PYTHON_CLASS_NAMESPACE_UNSUPPORTED"),
    ("class A(**options):\n    value = 1", "PYTHON_CLASS_NAMESPACE_UNSUPPORTED"),
    ("value: int = 1", "PYTHON_VARIABLE_ANNOTATION_SCOPE_UNSUPPORTED"),
    ("class A:\n    value: int", "PYTHON_VARIABLE_ANNOTATION_SCOPE_UNSUPPORTED"),
    ("def f():\n    value: int = 1\n    return value", "PYTHON_VARIABLE_ANNOTATION_SCOPE_UNSUPPORTED"),
])
def test_ordered_class_bindings_dynamic_namespace_and_annotations_are_explicitly_unavailable(code, category):
    result = canonical(code)
    assert result.mode == "lexical-fallback"
    assert result.identifiers == []
    assert result.tokens == [token.value for token in tokenize_code_with_locations(code, "python")]
    assert result.reason.startswith(category + ":")


@pytest.mark.parametrize("code,category", [
    ("xs = [x for x in range(3)]", "PYTHON_COMPREHENSION_SCOPE_UNSUPPORTED"),
    ("xs = {x for x in range(3)}", "PYTHON_COMPREHENSION_SCOPE_UNSUPPORTED"),
    ("xs = {x: x + 1 for x in range(3)}", "PYTHON_COMPREHENSION_SCOPE_UNSUPPORTED"),
    ("xs = (x for x in range(3))", "PYTHON_COMPREHENSION_SCOPE_UNSUPPORTED"),
    ("value = 1\ndef f():\n    global value\n    value = 2", "PYTHON_GLOBAL_SCOPE_UNSUPPORTED"),
    ("def f():\n    value = 1\n    def g():\n        nonlocal value\n        return value", "PYTHON_NONLOCAL_SCOPE_UNSUPPORTED"),
    ("f = lambda: (value := 1)", "PYTHON_NAMED_EXPRESSION_SCOPE_UNSUPPORTED"),
    ("try:\n    pass\nexcept ValueError as error:\n    print(error)", "PYTHON_EXCEPTION_BINDING_UNSUPPORTED"),
    ("match data:\n    case name:\n        print(name)", "PYTHON_MATCH_CAPTURE_UNSUPPORTED"),
    ("match data:\n    case [*rest]:\n        print(rest)", "PYTHON_MATCH_CAPTURE_UNSUPPORTED"),
    ("match data:\n    case {**rest}:\n        print(rest)", "PYTHON_MATCH_CAPTURE_UNSUPPORTED"),
    ("import math as helpers\nprint(helpers.pi)", "PYTHON_IMPORT_BINDING_UNSUPPORTED"),
    ("from math import pi as value", "PYTHON_IMPORT_BINDING_UNSUPPORTED"),
    ("from math import *", "PYTHON_IMPORT_BINDING_UNSUPPORTED"),
    ("def f(value: int):\n    return value", "PYTHON_FUNCTION_ANNOTATION_SCOPE_UNSUPPORTED"),
    ("def f(value) -> int:\n    return value", "PYTHON_FUNCTION_ANNOTATION_SCOPE_UNSUPPORTED"),
])
def test_unsupported_binding_forms_return_raw_tokens_without_scope_evidence(code, category):
    tokens = tokenize_code_with_locations(code, "python")
    result = canonical(code)
    assert result.mode == "lexical-fallback"
    assert result.tokens == [token.value for token in tokens]
    assert result.identifiers == []
    assert result.reason.startswith(category + ":")
    assert "at line " in result.reason


def test_syntax_failure_returns_explicit_reason_and_no_scope_evidence():
    result = canonical("def f(:\n    pass")
    assert result.mode == "lexical-fallback"
    assert result.identifiers == []
    assert result.reason.startswith("PYTHON_SYNTAX_ERROR:")
