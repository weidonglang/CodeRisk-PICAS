"""Hand-marked binding gold and an independent spelling action, not a detector.

Markers are authored by hand. Rendering computes offsets, never binding identity.
This module deliberately has no dependency on the production binder or tokenizer.
"""
from __future__ import annotations

import ast
import io
import keyword
import re
import symtable
import tokenize
from dataclasses import dataclass


MARKER = re.compile(r"\{\{([a-z0-9_]+):([A-Za-z_][A-Za-z_0-9]*)\}\}")
JAVA_LEXEMES = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_$][A-Za-z_$0-9]*', re.S)


@dataclass(frozen=True)
class Gold:
    id: str
    language: str
    marked: str
    expected: dict[str, str]
    domain: tuple[str, ...]
    symbols: tuple[tuple[tuple[str, ...], str, str], ...] = ()


GOLD = (
    Gold('py-keywords', 'python',
         'def {{f:fold}}({{p:value}}, *, {{s:step}}=1):\n'
         '    {{r:result}} = {{p:value}} + {{s:step}}\n'
         '    return {{r:result}}\n{{f:fold}}({{p:value}}=2, {{s:step}}=3)\n',
         {'f': 'MODULE::FUNC_1', 'p': 'MODULE/FUNC_1_1::PARAM_1',
          's': 'MODULE/FUNC_1_1::PARAM_2', 'r': 'MODULE/FUNC_1_1::VAR_1'},
         ('fold', 'value', 'step', 'result', 'spareone', 'sparetwo'),
         ((('fold',), 'value', 'parameter'), (('fold',), 'result', 'local'))),
    Gold('py-shadow-closure', 'python',
         'def {{f:outer}}({{p:value}}):\n'
         '    {{r:total}} = {{p:value}}\n'
         '    def {{g:inner}}({{q:value}}):\n'
         '        return {{q:value}} + {{r:total}}\n'
         '    return {{g:inner}}({{q:value}}={{r:total}})\n',
         {'f': 'MODULE::FUNC_1', 'p': 'MODULE/FUNC_1_1::PARAM_1',
          'r': 'MODULE/FUNC_1_1::VAR_1', 'g': 'MODULE/FUNC_1_1::FUNC_1',
          'q': 'MODULE/FUNC_1_1/FUNC_1_1::PARAM_1'},
         ('outer', 'inner', 'value', 'total', 'spareone', 'sparetwo'),
         ((('outer', 'inner'), 'total', 'free'), (('outer', 'inner'), 'value', 'parameter'))),
    Gold('py-default-scope', 'python',
         '{{a:seed}} = 9\ndef {{f:fold}}({{p:seed}}={{a:seed}}):\n    return {{p:seed}}\n',
         {'a': 'MODULE::VAR_1', 'f': 'MODULE::FUNC_1', 'p': 'MODULE/FUNC_1_1::PARAM_1'},
         ('seed', 'fold', 'spareone', 'sparetwo', 'sparethree', 'sparefour'),
         (((), 'seed', 'local'), (('fold',), 'seed', 'parameter'))),
    Gold('py-lambda-default', 'python',
         '{{a:base}} = 9\n{{h:handler}} = lambda {{p:value}}={{a:base}}: {{p:value}} + {{a:base}}\n',
         {'a': 'MODULE::VAR_1', 'h': 'MODULE::VAR_2', 'p': 'MODULE/LAMBDA_1::PARAM_1'},
         ('base', 'handler', 'value', 'spareone', 'sparetwo', 'sparethree'),
         ((('lambda',), 'value', 'parameter'), (('lambda',), 'base', 'global'))),
    Gold('py-class-default', 'python',
         '{{a:seed}} = 9\nclass {{c:Box}}:\n    {{b:seed}} = 2\n'
         '    def {{f:fold}}({{s:self}}, {{p:value}}={{b:seed}}):\n'
         '        return {{p:value}} + {{a:seed}}\n',
         {'a': 'MODULE::VAR_1', 'c': 'MODULE::CLASS_1', 'b': 'MODULE/CLASS_1_1::VAR_1',
          'f': 'MODULE/CLASS_1_1::FUNC_1', 's': 'MODULE/CLASS_1_1/FUNC_1_1::PARAM_1',
          'p': 'MODULE/CLASS_1_1/FUNC_1_1::PARAM_2'},
         ('seed', 'fold', 'value', 'spareone', 'sparetwo', 'sparethree'),
         ((('Box', 'fold'), 'seed', 'global'), (('Box', 'fold'), 'value', 'parameter'))),
    Gold('py-forward-keyword', 'python',
         '{{f:fold}}({{p:value}}=2)\ndef {{f:fold}}({{p:value}}):\n    return {{p:value}} + 1\n',
         {'f': 'MODULE::FUNC_1', 'p': 'MODULE/FUNC_1_1::PARAM_1'},
         ('fold', 'value', 'spareone', 'sparetwo', 'sparethree', 'sparefour'),
         ((('fold',), 'value', 'parameter'),)),
    Gold('py-shared-spelling', 'python',
         'def {{f:fold}}({{p:value}}):\n    return {{p:value}} + 1\n'
         'def {{g:process}}({{q:value}}):\n    return {{q:value}} + 2\n',
         {'f': 'MODULE::FUNC_1', 'g': 'MODULE::FUNC_2',
          'p': 'MODULE/FUNC_1_1::PARAM_1', 'q': 'MODULE/FUNC_2_2::PARAM_1'},
         ('fold', 'process', 'value', 'spareone', 'sparetwo', 'sparethree'),
         ((('fold',), 'value', 'parameter'), (('process',), 'value', 'parameter'))),
    Gold('py-unicode-offset', 'python',
         '{{a:message}} = "\u4e2d"; {{b:value}} = 1\nprint({{a:message}}, {{b:value}})\n',
         {'a': 'MODULE::VAR_1', 'b': 'MODULE::VAR_2'},
         ('message', 'value', 'spareone', 'sparetwo', 'sparethree', 'sparefour'),
         (((), 'message', 'local'), ((), 'value', 'local'))),
    Gold('py-variadic-declarations', 'python',
         'def {{f:fold}}(*{{a:items}}, {{b:step}}=1, **{{c:options}}):\n'
         '    {{r:total}} = len({{a:items}}) + {{b:step}}\n    return {{r:total}}\n',
         {'f': 'MODULE::FUNC_1', 'a': 'MODULE/FUNC_1_1::PARAM_1', 'b': 'MODULE/FUNC_1_1::PARAM_2',
          'c': 'MODULE/FUNC_1_1::PARAM_3', 'r': 'MODULE/FUNC_1_1::VAR_1'},
         ('fold', 'items', 'step', 'options', 'total', 'spareone'),
         ((('fold',), 'items', 'parameter'), (('fold',), 'options', 'parameter'))),
    Gold('java-declaration-point', 'java',
         'class {{c:Main}} {\n    int {{a:value}} = 9;\n    int {{f:fold}}() {\n'
         '        int {{b:first}} = {{a:value}};\n        int {{d:value}} = 2;\n'
         '        return {{b:first}} + {{d:value}} + this.{{a:value}};\n    }\n}\n',
         {'c': 'ROOT::CLASS_1', 'a': 'ROOT/SCOPE_1::VAR_1', 'f': 'ROOT/SCOPE_1::FUNC_1',
          'b': 'ROOT/SCOPE_1/SCOPE_1::VAR_1', 'd': 'ROOT/SCOPE_1/SCOPE_1::VAR_2'},
         ('value', 'first', 'fold', 'spareone', 'sparetwo', 'sparethree')),
    Gold('java-block-locals', 'java',
         'class {{c:Main}} {\n    int {{f:fold}}(int {{p:value}}) {\n'
         '        if ({{p:value}} > 0) { int {{a:part}} = {{p:value}}; System.out.println({{a:part}}); }\n'
         '        else { int {{b:part}} = -{{p:value}}; System.out.println({{b:part}}); }\n'
         '        return {{p:value}};\n    }\n}\n',
         {'c': 'ROOT::CLASS_1', 'f': 'ROOT/SCOPE_1::FUNC_1', 'p': 'ROOT/SCOPE_1/SCOPE_1::PARAM_1',
          'a': 'ROOT/SCOPE_1/SCOPE_1/SCOPE_1::VAR_1', 'b': 'ROOT/SCOPE_1/SCOPE_1/SCOPE_2::VAR_1'},
         ('fold', 'value', 'part', 'spareone', 'sparetwo', 'sparethree')),
    Gold('java-internal-external-call', 'java',
         'class {{c:Main}} {\n    int {{f:fold}}(int {{p:value}}) { return {{p:value}} + 1; }\n'
         '    int {{g:process}}(int {{q:value}}) { return {{f:fold}}({{q:value}}) + Math.abs(-1); }\n}\n',
         {'c': 'ROOT::CLASS_1', 'f': 'ROOT/SCOPE_1::FUNC_1', 'g': 'ROOT/SCOPE_1::FUNC_2',
          'p': 'ROOT/SCOPE_1/SCOPE_1::PARAM_1', 'q': 'ROOT/SCOPE_1/SCOPE_2::PARAM_1'},
         ('fold', 'process', 'value', 'spareone', 'sparetwo', 'sparethree')),
)


def render(gold: Gold) -> tuple[str, list[dict]]:
    parts, occurrences, offset, line, column = [], [], 0, 1, 0
    for match in MARKER.finditer(gold.marked):
        prefix = gold.marked[offset:match.start()]
        parts.append(prefix)
        if '\n' in prefix:
            line += prefix.count('\n')
            column = len(prefix.rsplit('\n', 1)[1])
        else:
            column += len(prefix)
        binding, name = match.groups()
        if binding not in gold.expected:
            raise ValueError('Unspecified handwritten binding: ' + binding)
        occurrences.append({'binding': binding, 'name': name, 'line': line, 'column': column,
                            'canonical': gold.expected[binding]})
        parts.append(name)
        column += len(name)
        offset = match.end()
    parts.append(gold.marked[offset:])
    return ''.join(parts), occurrences


def names(code: str, language: str) -> list[tuple[str, int, int]]:
    if language == 'python':
        return [(t.string, *t.start) for t in tokenize.generate_tokens(io.StringIO(code).readline)
                if t.type == tokenize.NAME]
    result = []
    for match in JAVA_LEXEMES.finditer(code):
        if re.fullmatch(r'[A-Za-z_$][A-Za-z_$0-9]*', match.group()):
            prefix = code[:match.start()]
            result.append((match.group(), prefix.count('\n') + 1, len(prefix.rsplit('\n', 1)[-1])))
    return result


def validate_gold(gold: Gold) -> None:
    code, occurrences = render(gold)
    lexical = {(line, column): name for name, line, column in names(code, gold.language)}
    annotated = {(r['line'], r['column']): r['name'] for r in occurrences}
    if any(lexical.get(location) != name for location, name in annotated.items()):
        raise ValueError('Handwritten marker does not point to an identifier')
    if any(location not in annotated for location, name in lexical.items() if name in gold.domain):
        raise ValueError('Movable spelling has an unmarked occurrence')
    if set(gold.expected) != {r['binding'] for r in occurrences}:
        raise ValueError('Binding without an occurrence')
    if gold.language == 'python':
        ast.parse(code)
        table = symtable.symtable(code, gold.id, 'exec')
        for path, name, flag in gold.symbols:
            child = table
            for scope_name in path:
                matches = [c for c in child.get_children() if c.get_name() == scope_name]
                if len(matches) != 1:
                    raise ValueError('Ambiguous independent symtable scope')
                child = matches[0]
            if not getattr(child.lookup(name), 'is_' + flag)():
                raise ValueError('Independent symtable disagrees with handwritten gold')


def action(code: str, language: str, domain: tuple[str, ...], mapping: dict[str, str]) -> str:
    if set(mapping) != set(domain) or set(mapping.values()) != set(domain):
        raise ValueError('INVALID_CAPTURE: action must be a bijection of the fixed domain')
    if any(not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', n) or keyword.iskeyword(n) for n in domain):
        raise ValueError('REJECTED_UNSUPPORTED: illegal name domain')
    lines = code.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits = [(offsets[line - 1] + column, name, mapping[name])
             for name, line, column in names(code, language) if name in domain]
    for position, old, new in reversed(edits):
        code = code[:position] + new + code[position + len(old):]
    return code


BOUNDARIES = (
    ('dynamic-reflection', 'python', "def f(value):\n    return globals()['value']\n", 'REJECTED_UNSUPPORTED', 'PYTHON_DYNAMIC_NAME_ACCESS_UNSUPPORTED'),
    ('indirect-keyword', 'python', 'def f(value):\n    return value\nalias=f\nalias(value=1)\n', 'REJECTED_UNSUPPORTED', 'PYTHON_INDIRECT_KEYWORD_CALL_UNSUPPORTED'),
    ('comprehension', 'python', 'def f(values):\n    return [value for value in values]\n', 'REJECTED_UNSUPPORTED', 'PYTHON_COMPREHENSION_SCOPE_UNSUPPORTED'),
    ('nonlocal', 'python', 'def f():\n    value=1\n    def g():\n        nonlocal value\n        return value\n', 'REJECTED_UNSUPPORTED', 'PYTHON_NONLOCAL_SCOPE_UNSUPPORTED'),
    ('syntax-error', 'python', 'def f(:\n    return 1\n', 'PARSER_FAILURE', 'PYTHON_SYNTAX_ERROR'),
    ('unbalanced-java', 'java', 'class Main { int f() { return 1;', 'PARSER_FAILURE', 'JAVA_PARSE_UNAVAILABLE'),
    ('for-shadow-field', 'java', 'class Main { int value=7; int f() { for (int value=0; value<1; value++) {} return value; } }', 'REJECTED_UNSUPPORTED', 'JAVA_HEADER_SHADOW_BINDING_UNSUPPORTED'),
    ('opaque-external-wrapper', 'python', 'def f(value):\n    return inspect_name("value")\n', 'ORACLE_UNCERTAIN', 'External wrapper contract unknown; blacklist is not complete'),
    ('java-overload', 'java', 'class Main { int f(int value) {return value;} double f(double value) {return value;} }', 'ORACLE_UNCERTAIN', 'No Java type or overload resolution oracle'),
)
