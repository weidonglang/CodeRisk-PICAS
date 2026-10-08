from __future__ import annotations

import ast
import keyword
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Protocol

from app.analyzers.java_source import balanced_tokens, mask_comments


class SourceToken(Protocol):
    value: str
    line: int
    column: int


@dataclass(frozen=True)
class CanonicalAnalysis:
    tokens: list[str]
    identifiers: list[dict[str, object]]
    mode: str


@dataclass(frozen=True)
class IdentifierMappingAnalysis:
    mappings: list[dict[str, object]]
    similarity: float
    coverage: float
    consistency: float


@dataclass
class _Symbol:
    raw_name: str
    kind: str
    canonical_name: str
    scope_path: str

    @property
    def scoped_name(self) -> str:
        return f"{self.scope_path}::{self.canonical_name}"


@dataclass
class _Scope:
    path: str
    parent: _Scope | None
    bindings: dict[str, _Symbol] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    child_count: int = 0

    def child(self, label: str) -> _Scope:
        self.child_count += 1
        return _Scope(f"{self.path}/{label}_{self.child_count}", self)

    def declare(self, raw_name: str, kind: str) -> _Symbol:
        existing = self.bindings.get(raw_name)
        if existing is not None:
            return existing
        self.counters[kind] += 1
        symbol = _Symbol(raw_name, kind, f"{kind}_{self.counters[kind]}", self.path)
        self.bindings[raw_name] = symbol
        return symbol

    def resolve(self, raw_name: str) -> _Symbol | None:
        scope: _Scope | None = self
        while scope is not None:
            if raw_name in scope.bindings:
                return scope.bindings[raw_name]
            scope = scope.parent
        return None


def canonicalize_code(code: str, language: str, tokens: list[SourceToken]) -> CanonicalAnalysis:
    normalized = language.lower()
    if normalized in {"python", "py"}:
        return _canonicalize_python(code, tokens)
    if normalized == "java":
        return _canonicalize_java(code, tokens)
    if normalized in {"c", "html", "htm"}:
        from app.analyzers.structured_languages import analyze_source
        language_name = 'html' if normalized == 'htm' else normalized
        result = analyze_source(code, language_name)
        if not result.parsed or not result.normalization_available:
            return CanonicalAnalysis([token.value for token in tokens], [], 'lexical-fallback')
        return CanonicalAnalysis(result.canonical_tokens, result.identifiers,
                                 'scope-aware-c-subset' if language_name == 'c' else 'html-structure-canonical')
    return _lexical_fallback(tokens, normalized)


def build_identifier_mapping(
    left: CanonicalAnalysis,
    right: CanonicalAnalysis,
    limit: int = 20,
) -> IdentifierMappingAnalysis:
    left_symbols = _group_symbols(left.identifiers)
    right_symbols = _group_symbols(right.identifiers)
    common_keys = sorted(left_symbols.keys() & right_symbols.keys())
    total_symbols = max(len(left_symbols), len(right_symbols), 1)
    mappings: list[dict[str, object]] = []
    consistent = 0
    for key in common_keys:
        left_items = left_symbols[key]
        right_items = right_symbols[key]
        left_name = str(left_items[0]["rawName"])
        right_name = str(right_items[0]["rawName"])
        left_names = {str(item["rawName"]) for item in left_items}
        right_names = {str(item["rawName"]) for item in right_items}
        is_consistent = len(left_names) == 1 and len(right_names) == 1
        if is_consistent:
            consistent += 1
        if left_name == right_name or len(mappings) >= max(limit, 0):
            continue
        first_left = left_items[0]
        first_right = right_items[0]
        mappings.append(
            {
                "mappingType": _mapping_type(str(first_left["kind"])),
                "kind": str(first_left["kind"]),
                "canonicalName": str(first_left["canonicalName"]),
                "scopePath": str(first_left["scopePath"]),
                "submissionAName": left_name,
                "submissionBName": right_name,
                "submissionALine": int(first_left["line"]),
                "submissionBLine": int(first_right["line"]),
                "occurrenceA": len(left_items),
                "occurrenceB": len(right_items),
                "confidence": round(min(len(left_items), len(right_items)) / max(len(left_items), len(right_items)), 6),
            }
        )
    coverage = len(common_keys) / total_symbols
    consistency = consistent / max(len(common_keys), 1)
    similarity = coverage * consistency
    return IdentifierMappingAnalysis(
        mappings=mappings,
        similarity=round(similarity, 6),
        coverage=round(coverage, 6),
        consistency=round(consistency, 6),
    )


class _PythonIndexer:
    def __init__(self, tokens: list[SourceToken], code: str) -> None:
        self.tokens = tokens
        self.lines = code.splitlines()
        self.overrides: dict[tuple[int, int], _Symbol] = {}

    def _location(self, line: int, byte_column: int) -> tuple[int, int]:
        # AST offsets are UTF-8 bytes; tokenize offsets are Unicode characters.
        prefix = self.lines[line - 1].encode('utf-8')[:byte_column]
        return line, len(prefix.decode('utf-8'))

    def index(self, tree: ast.AST) -> dict[tuple[int, int], _Symbol]:
        module = _Scope("MODULE", None)
        self._predeclare_scope(module, list(getattr(tree, "body", [])), [])
        for node in getattr(tree, "body", []):
            self._walk(node, module)
        return self.overrides

    def _predeclare_scope(self, scope: _Scope, body: list[ast.stmt], parameters: list[ast.arg]) -> None:
        declarations: list[tuple[int, int, str, str]] = []
        for index, argument in enumerate(parameters):
            declarations.append((int(argument.lineno), int(argument.col_offset), argument.arg, "PARAM"))
        collector = _PythonDeclarationCollector()
        for node in body:
            collector.visit(node)
        declarations.extend(collector.declarations)
        for _, _, name, kind in sorted(declarations):
            scope.declare(name, kind)

    def _walk(self, node: ast.AST, scope: _Scope) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbol = scope.declare(node.name, "FUNC")
            self._bind_named_token(node.lineno, node.col_offset, node.name, symbol)
            for decorator in node.decorator_list:
                self._walk(decorator, scope)
            for default in [*node.args.defaults, *node.args.kw_defaults]:
                if default is not None:
                    self._walk(default, scope)
            child = scope.child(symbol.canonical_name)
            parameters = [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]
            if node.args.vararg:
                parameters.append(node.args.vararg)
            if node.args.kwarg:
                parameters.append(node.args.kwarg)
            self._predeclare_scope(child, node.body, parameters)
            for argument in parameters:
                argument_symbol = child.declare(argument.arg, "PARAM")
                self.overrides[self._location(argument.lineno, argument.col_offset)] = argument_symbol
            for statement in node.body:
                self._walk(statement, child)
            return
        if isinstance(node, ast.ClassDef):
            symbol = scope.declare(node.name, "CLASS")
            self._bind_named_token(node.lineno, node.col_offset, node.name, symbol)
            for base in node.bases:
                self._walk(base, scope)
            child = scope.child(symbol.canonical_name)
            self._predeclare_scope(child, node.body, [])
            for statement in node.body:
                self._walk(statement, child)
            return
        if isinstance(node, ast.Lambda):
            child = scope.child("LAMBDA")
            parameters = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            self._predeclare_scope(child, [], parameters)
            for argument in parameters:
                self.overrides[self._location(argument.lineno, argument.col_offset)] = child.declare(argument.arg, "PARAM")
            self._walk(node.body, child)
            return
        if isinstance(node, ast.Name):
            symbol = scope.resolve(node.id)
            if symbol is not None:
                self.overrides[self._location(node.lineno, node.col_offset)] = symbol
            return
        for child in ast.iter_child_nodes(node):
            self._walk(child, scope)

    def _bind_named_token(self, line: int, column: int, raw_name: str, symbol: _Symbol) -> None:
        _, column = self._location(line, column)
        candidates = [
            token for token in self.tokens
            if token.line == line and token.column >= column and token.value == raw_name
        ]
        if candidates:
            token = min(candidates, key=lambda item: item.column)
            self.overrides[(token.line, token.column)] = symbol


class _PythonDeclarationCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.declarations: list[tuple[int, int, str, str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.declarations.append((node.lineno, node.col_offset, node.name, "FUNC"))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.declarations.append((node.lineno, node.col_offset, node.name, "FUNC"))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.declarations.append((node.lineno, node.col_offset, node.name, "CLASS"))

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.declarations.append((node.lineno, node.col_offset, node.id, "VAR"))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.declarations.append((node.lineno, node.col_offset, name, "VAR"))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = alias.asname or alias.name
            self.declarations.append((node.lineno, node.col_offset, name, "VAR"))


def _canonicalize_python(code: str, tokens: list[SourceToken]) -> CanonicalAnalysis:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _lexical_fallback(tokens, "python")
    overrides = _PythonIndexer(tokens, code).index(tree)
    return _apply_overrides(tokens, overrides, "scope-aware-python")


def _canonicalize_java(code: str, tokens: list[SourceToken]) -> CanonicalAnalysis:
    if mask_comments(code)[1] or not balanced_tokens(token.value for token in tokens) or not tokens:
        return _lexical_fallback(tokens, "java")
    values = [token.value for token in tokens]
    paths, parents, brace_children = _java_scope_paths(values)
    scopes: dict[str, _Scope] = {"ROOT": _Scope("ROOT", None)}
    for path in sorted(set(paths), key=lambda value: (value.count("/"), value)):
        if path == "ROOT":
            continue
        parent_path = parents[path]
        scopes[path] = _Scope(path, scopes[parent_path])

    declarations: dict[int, _Symbol] = {}
    parameter_indices: set[int] = set()
    class_body_paths: set[str] = set()

    for index, value in enumerate(values):
        if value == "class" and index + 1 < len(values) and _is_java_identifier(values[index + 1]):
            declarations[index + 1] = scopes[paths[index + 1]].declare(values[index + 1], "CLASS")
            body = _next_token_index(values, index + 2, "{")
            if body in brace_children:
                class_body_paths.add(brace_children[body])

    for index, value in enumerate(values):
        if not _is_java_identifier(value) or index + 1 >= len(values) or values[index + 1] != "(":
            continue
        close_index = _matching_token(values, index + 1, "(", ")")
        if close_index is None or not _is_java_method_declaration(values, index, close_index):
            continue
        symbol = scopes[paths[index]].declare(value, "FUNC")
        declarations[index] = symbol
        body_open = _next_token_index(values, close_index + 1, "{")
        body_path = brace_children.get(body_open, paths[index]) if body_open is not None else paths[index]
        for parameter_index in _java_parameter_names(values, index + 2, close_index):
            parameter_indices.add(parameter_index)
            declarations[parameter_index] = scopes[body_path].declare(values[parameter_index], "PARAM")

    excluded = set(declarations) | parameter_indices
    for index, value in enumerate(values):
        if index in excluded or not _is_java_identifier(value):
            continue
        if _looks_like_java_variable_declaration(values, index):
            declarations[index] = scopes[paths[index]].declare(value, "VAR")

    overrides: dict[tuple[int, int], _Symbol] = {}
    for index, token in enumerate(tokens):
        symbol = declarations.get(index)
        if symbol is None and _is_java_identifier(token.value):
            if index > 0 and values[index - 1] == '.':
                # Without type resolution, external object members must remain raw.
                if index > 1 and values[index - 2] == 'this':
                    scope = scopes[paths[index]]
                    while scope and scope.path not in class_body_paths:
                        scope = scope.parent
                    symbol = scope.bindings.get(token.value) if scope else None
            else:
                symbol = scopes[paths[index]].resolve(token.value)
        if symbol is not None:
            overrides[(token.line, token.column)] = symbol
    return _apply_overrides(tokens, overrides, "scope-aware-java")


def _apply_overrides(
    tokens: list[SourceToken],
    overrides: dict[tuple[int, int], _Symbol],
    mode: str,
) -> CanonicalAnalysis:
    canonical_tokens: list[str] = []
    identifiers: list[dict[str, object]] = []
    for position, token in enumerate(tokens):
        symbol = overrides.get((token.line, token.column))
        if symbol is None:
            canonical_tokens.append(token.value)
            continue
        canonical_tokens.append(symbol.scoped_name)
        identifiers.append(_identifier_item(token, position, symbol))
    return CanonicalAnalysis(canonical_tokens, identifiers, mode)


def _lexical_fallback(tokens: list[SourceToken], language: str) -> CanonicalAnalysis:
    counters: dict[str, int] = defaultdict(int)
    symbols: dict[tuple[str, str], _Symbol] = {}
    canonical_tokens: list[str] = []
    identifiers: list[dict[str, object]] = []
    values = [token.value for token in tokens]
    for position, token in enumerate(tokens):
        if not _is_identifier(token.value, language):
            canonical_tokens.append(token.value)
            continue
        previous = values[position - 1] if position > 0 else ""
        next_value = values[position + 1] if position + 1 < len(values) else ""
        kind = "CLASS" if previous == "class" else "FUNC" if previous == "def" or next_value == "(" else "VAR"
        key = (kind, token.value)
        if key not in symbols:
            counters[kind] += 1
            symbols[key] = _Symbol(token.value, kind, f"{kind}_{counters[kind]}", "FALLBACK")
        symbol = symbols[key]
        canonical_tokens.append(symbol.scoped_name)
        identifiers.append(_identifier_item(token, position, symbol))
    return CanonicalAnalysis(canonical_tokens, identifiers, "lexical-fallback")


def _identifier_item(token: SourceToken, position: int, symbol: _Symbol) -> dict[str, object]:
    return {
        "rawName": token.value,
        "canonicalName": symbol.canonical_name,
        "scopedCanonicalName": symbol.scoped_name,
        "scopePath": symbol.scope_path,
        "kind": symbol.kind,
        "line": token.line,
        "column": token.column,
        "position": position,
    }


def _group_symbols(items: list[dict[str, object]]) -> dict[tuple[str, str], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for item in items:
        grouped[(str(item["kind"]), str(item["scopedCanonicalName"]))].append(item)
    return grouped


def _mapping_type(kind: str) -> str:
    return {"VAR": "VARIABLE", "FUNC": "FUNCTION", "PARAM": "PARAMETER", "CLASS": "CLASS"}.get(kind, kind)


def _java_scope_paths(values: list[str]) -> tuple[list[str], dict[str, str], dict[int, str]]:
    stack = ["ROOT"]
    child_counts: dict[str, int] = defaultdict(int)
    parents: dict[str, str] = {}
    brace_children: dict[int, str] = {}
    paths: list[str] = []
    for index, value in enumerate(values):
        paths.append(stack[-1])
        if value == "{":
            parent = stack[-1]
            child_counts[parent] += 1
            child = f"{parent}/SCOPE_{child_counts[parent]}"
            parents[child] = parent
            brace_children[index] = child
            stack.append(child)
        elif value == "}" and len(stack) > 1:
            stack.pop()
    return paths, parents, brace_children


def _java_parameter_names(values: list[str], start: int, end: int) -> list[int]:
    result: list[int] = []
    segment_start = start
    depth = 0
    for index in range(start, end + 1):
        value = values[index] if index < end else ","
        if value in {"<", "["}:
            depth += 1
        elif value in {">", "]"}:
            depth = max(0, depth - 1)
        if value == "," and depth == 0:
            candidates = [
                pos for pos in range(segment_start, index)
                if _is_java_identifier(values[pos]) and values[pos] not in JAVA_MODIFIERS
            ]
            if candidates and any(values[pos] in JAVA_PRIMITIVE_TYPES for pos in range(segment_start, index)):
                result.append(candidates[-1])
            elif len(candidates) >= 2:
                result.append(candidates[-1])
            segment_start = index + 1
    return result


def _is_java_method_declaration(values: list[str], name_index: int, close_index: int) -> bool:
    previous = values[name_index - 1] if name_index > 0 else ""
    if previous in JAVA_CONTROL_WORDS or previous in {"new", ".", "@", "(", "=", ",", "->"}:
        return False
    index = close_index + 1
    if index < len(values) and values[index] == 'throws':
        index += 1
        while index < len(values) and (_is_java_identifier(values[index]) or values[index] in {'.', ','}):
            index += 1
    return index < len(values) and values[index] == "{"


def _looks_like_java_variable_declaration(values: list[str], index: int) -> bool:
    if index == 0:
        return False
    previous = values[index - 1]
    next_value = values[index + 1] if index + 1 < len(values) else ""
    if next_value == "(" or previous in {".", "class", "interface", "enum", "package", "import"}:
        return False
    if previous in JAVA_PRIMITIVE_TYPES:
        return True
    before_previous = values[index - 2] if index > 1 else ""
    return _is_java_identifier(previous) and before_previous in {"{", ";", "(", ","}


def _matching_token(values: list[str], start: int, opening: str, closing: str) -> int | None:
    depth = 0
    for index in range(start, len(values)):
        if values[index] == opening:
            depth += 1
        elif values[index] == closing:
            depth -= 1
            if depth == 0:
                return index
    return None


def _next_token_index(values: list[str], start: int, target: str) -> int | None:
    for index in range(start, len(values)):
        if values[index] == target:
            return index
        if values[index] == ";":
            return None
    return None


def _is_java_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value)) and value not in JAVA_KEYWORDS


def _is_identifier(value: str, language: str) -> bool:
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value):
        return False
    if language in {"python", "py"}:
        return not keyword.iskeyword(value)
    return value not in JAVA_KEYWORDS


JAVA_PRIMITIVE_TYPES = {"boolean", "byte", "char", "double", "float", "int", "long", "short", "String", "var"}
JAVA_MODIFIERS = {"final", "volatile", "transient", "public", "private", "protected", "static"}
JAVA_CONTROL_WORDS = {"if", "for", "while", "switch", "catch", "return", "throw", "synchronized"}
JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
    "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float",
    "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native",
    "new", "package", "private", "protected", "public", "return", "short", "static", "strictfp", "super",
    "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void", "volatile", "while",
    "true", "false", "null",
}
