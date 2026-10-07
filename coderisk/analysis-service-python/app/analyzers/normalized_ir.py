from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

IR_VERSION = "normalized-ir-java-python-subset-v0.1"
SUPPORTED_LANGUAGES = {"java", "python"}


@dataclass(frozen=True)
class IrNode:
    kind: str
    line: int


@dataclass(frozen=True)
class NormalizedIr:
    language: str
    parsed: bool
    supported: bool
    nodes: list[IrNode]
    coverage: float
    warnings: list[str]
    error: str = ""


@dataclass(frozen=True)
class IrComparison:
    comparable: bool
    similarity: float
    left: NormalizedIr
    right: NormalizedIr
    fragments: list[dict[str, object]]
    reason: str = ""


@dataclass(frozen=True)
class _JavaToken:
    value: str
    line: int


class _PythonIrVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.nodes: list[IrNode] = [IrNode("PROGRAM", 1)]
        self.supported_count = 1

    def add(self, kind: str, node: ast.AST) -> None:
        self.nodes.append(IrNode(kind, max(1, int(getattr(node, "lineno", 1) or 1))))
        self.supported_count += 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.add("FUNCTION", node)
        for statement in node.body:
            self.visit(statement)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.add("ASSIGN", node)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.add("ASSIGN", node)
        if node.value is not None:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.add("ASSIGN", node)
        self._add_operator(node.op, node)
        self.visit(node.value)

    def visit_If(self, node: ast.If) -> None:
        self.add("IF", node)
        self.visit(node.test)
        for statement in node.body:
            self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)

    def visit_For(self, node: ast.For) -> None:
        self.add("LOOP", node)
        for statement in node.body:
            self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)

    def visit_While(self, node: ast.While) -> None:
        self.add("LOOP", node)
        self.visit(node.test)
        for statement in node.body:
            self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)

    def visit_Call(self, node: ast.Call) -> None:
        name = _python_call_name(node.func)
        if name == "input":
            self.add("INPUT", node)
        elif name == "print":
            self.add("OUTPUT", node)
        elif name not in {"range", "len", "int", "float", "str"}:
            self.add("CALL", node)
        for argument in node.args:
            self.visit(argument)

    def visit_Return(self, node: ast.Return) -> None:
        self.add("RETURN", node)
        if node.value is not None:
            self.visit(node.value)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        self._add_operator(node.op, node)
        self.visit(node.left)
        self.visit(node.right)

    def visit_Compare(self, node: ast.Compare) -> None:
        for operator in node.ops:
            self._add_operator(operator, node)
        self.visit(node.left)
        for comparator in node.comparators:
            self.visit(comparator)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.add("LOGIC_AND" if isinstance(node.op, ast.And) else "LOGIC_OR", node)
        for value in node.values:
            self.visit(value)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        if isinstance(node.op, ast.USub):
            self.add("ARITH_NEGATE", node)
        self.visit(node.operand)

    def _add_operator(self, operator: ast.AST, node: ast.AST) -> None:
        kind = _PYTHON_OPERATOR_KINDS.get(type(operator))
        if kind:
            self.add(kind, node)


def normalize_to_ir(code: str, language: str) -> NormalizedIr:
    normalized_language = _normalize_language(language)
    if normalized_language == "python":
        return _normalize_python(code)
    if normalized_language == "java":
        return _normalize_java(code)
    return NormalizedIr(
        normalized_language,
        False,
        False,
        [],
        0.0,
        [],
        f"Experimental normalized IR does not support language: {language}",
    )


def compare_normalized_ir(
    code_a: str,
    language_a: str,
    code_b: str,
    language_b: str,
) -> IrComparison:
    left = normalize_to_ir(code_a, language_a)
    right = normalize_to_ir(code_b, language_b)
    language_pair = {left.language, right.language}
    if language_pair != SUPPORTED_LANGUAGES:
        return IrComparison(False, 0.0, left, right, [], "Only Java-Python pairs are supported in V4 Phase 1.")
    if not left.parsed or not right.parsed:
        return IrComparison(False, 0.0, left, right, [], "At least one source could not be parsed for experimental IR.")
    if not left.supported or not right.supported:
        return IrComparison(False, 0.0, left, right, [], "IR mapping coverage is below the experimental support boundary.")

    left_kinds = [node.kind for node in left.nodes]
    right_kinds = [node.kind for node in right.nodes]
    sequence_score = SequenceMatcher(None, left_kinds, right_kinds, autojunk=False).ratio()
    ngram_score = _jaccard(_ngrams(left_kinds), _ngrams(right_kinds))
    feature_score = _jaccard({(item,) for item in left_kinds}, {(item,) for item in right_kinds})
    alignment = (0.55 * sequence_score) + (0.30 * ngram_score) + (0.15 * feature_score)
    minimum_length = min(len(left_kinds), len(right_kinds))
    distinct_count = min(len(set(left_kinds)), len(set(right_kinds)))
    specificity = min(1.0, minimum_length / 8.0) * min(1.0, distinct_count / 5.0)
    coverage_factor = 0.75 + (0.25 * min(left.coverage, right.coverage))
    similarity = round(alignment * (0.45 + (0.55 * specificity)) * coverage_factor, 6)
    return IrComparison(
        True,
        similarity,
        left,
        right,
        _matching_fragments(left.nodes, right.nodes),
    )


def _normalize_python(code: str) -> NormalizedIr:
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return NormalizedIr(
            "python",
            False,
            False,
            [],
            0.0,
            [],
            f"Python syntax error at line {error.lineno}: {error.msg}",
        )

    unsupported = [node for node in ast.walk(tree) if isinstance(node, _PYTHON_UNSUPPORTED_NODES)]
    visitor = _PythonIrVisitor()
    visitor.visit(tree)
    total = visitor.supported_count + len(unsupported)
    coverage = round(visitor.supported_count / total, 6) if total else 0.0
    warnings = sorted({f"Unsupported Python construct: {type(node).__name__}" for node in unsupported})
    supported = len(visitor.nodes) >= 4 and coverage >= 0.50
    if len(visitor.nodes) < 4:
        warnings.append("Too few mapped operations for reliable experimental IR comparison.")
    return NormalizedIr("python", True, supported, visitor.nodes, coverage, warnings)


def _normalize_java(code: str) -> NormalizedIr:
    stripped = _strip_java_comments(code)
    if not _balanced_delimiters(stripped):
        return NormalizedIr("java", False, False, [], 0.0, [], "Java delimiters are not balanced")
    tokens = _java_tokens(stripped)
    if not tokens:
        return NormalizedIr("java", False, False, [], 0.0, [], "No Java tokens found")

    nodes: list[IrNode] = [IrNode("PROGRAM", 1)]
    unsupported: list[str] = []
    for_header_end = -1
    index = 0
    while index < len(tokens):
        item = tokens[index]
        value = item.value
        if value in _JAVA_UNSUPPORTED_KEYWORDS:
            unsupported.append(f"Unsupported Java construct: {value}")
        if index <= for_header_end:
            index += 1
            continue
        if value == "for":
            nodes.append(IrNode("LOOP", item.line))
            opening = _next_token(tokens, index, "(")
            if opening >= 0:
                for_header_end = _matching_token(tokens, opening, "(", ")")
        elif value in {"while", "do"}:
            nodes.append(IrNode("LOOP", item.line))
        elif value == "if":
            nodes.append(IrNode("IF", item.line))
        elif value == "return":
            nodes.append(IrNode("RETURN", item.line))
        elif _is_java_method_declaration(tokens, index):
            nodes.append(IrNode("FUNCTION", item.line))
        elif _is_java_input_call(tokens, index):
            nodes.append(IrNode("INPUT", item.line))
        elif _is_java_output_call(tokens, index):
            nodes.append(IrNode("OUTPUT", item.line))
        elif value in _ASSIGNMENT_OPERATORS:
            nodes.append(IrNode("ASSIGN", item.line))
            if value != "=":
                nodes.append(IrNode(_JAVA_OPERATOR_KINDS[value[0]], item.line))
        elif value in {"++", "--"}:
            nodes.append(IrNode("ASSIGN", item.line))
            nodes.append(IrNode("ARITH_ADD" if value == "++" else "ARITH_SUBTRACT", item.line))
        elif value in _JAVA_OPERATOR_KINDS:
            nodes.append(IrNode(_JAVA_OPERATOR_KINDS[value], item.line))
        elif _is_java_call(tokens, index):
            nodes.append(IrNode("CALL", item.line))
        index += 1

    unsupported_count = len(unsupported)
    total = len(nodes) + unsupported_count
    coverage = round(len(nodes) / total, 6) if total else 0.0
    warnings = sorted(set(unsupported))
    supported = len(nodes) >= 4 and coverage >= 0.50
    if len(nodes) < 4:
        warnings.append("Too few mapped operations for reliable experimental IR comparison.")
    return NormalizedIr("java", True, supported, nodes, coverage, warnings)


def _matching_fragments(left: list[IrNode], right: list[IrNode]) -> list[dict[str, object]]:
    matcher = SequenceMatcher(
        None,
        [node.kind for node in left],
        [node.kind for node in right],
        autojunk=False,
    )
    fragments: list[dict[str, object]] = []
    for block in matcher.get_matching_blocks():
        if block.size < 2:
            continue
        left_block = left[block.a : block.a + block.size]
        right_block = right[block.b : block.b + block.size]
        fragments.append(
            {
                "nodes": [node.kind for node in left_block],
                "submissionAStartLine": left_block[0].line,
                "submissionAEndLine": left_block[-1].line,
                "submissionBStartLine": right_block[0].line,
                "submissionBEndLine": right_block[-1].line,
            }
        )
        if len(fragments) >= 5:
            break
    return fragments


def _python_call_name(function: ast.expr) -> str:
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return ""


def _normalize_language(language: str) -> str:
    lowered = language.strip().lower()
    return "python" if lowered == "py" else lowered


def _ngrams(values: list[str]) -> set[tuple[str, ...]]:
    if not values:
        return set()
    size = 2 if len(values) >= 2 else 1
    return {tuple(values[index : index + size]) for index in range(len(values) - size + 1)}


def _jaccard(left: set[tuple[str, ...]], right: set[tuple[str, ...]]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _java_tokens(code: str) -> list[_JavaToken]:
    tokens: list[_JavaToken] = []
    last_index = 0
    line = 1
    for match in _JAVA_TOKEN_PATTERN.finditer(code):
        line += code.count("\n", last_index, match.start())
        tokens.append(_JavaToken(match.group(0), line))
        last_index = match.end()
    return tokens


def _is_java_method_declaration(tokens: list[_JavaToken], index: int) -> bool:
    if not _is_identifier(tokens[index].value) or _value(tokens, index + 1) != "(":
        return False
    previous = _value(tokens, index - 1)
    if previous in {".", "new", "if", "for", "while", "switch", "catch", "return", "="}:
        return False
    closing = _matching_token(tokens, index + 1, "(", ")")
    if closing < 0:
        return False
    cursor = closing + 1
    if _value(tokens, cursor) == "throws":
        cursor += 1
        while cursor < len(tokens) and _value(tokens, cursor) != "{":
            cursor += 1
    return _value(tokens, cursor) == "{" and (
        previous in _JAVA_TYPE_TOKENS or _is_identifier(previous) or previous in {">", "]"}
    )


def _is_java_input_call(tokens: list[_JavaToken], index: int) -> bool:
    value = tokens[index].value
    if _value(tokens, index - 1) != ".":
        return False
    return (value.startswith("next") or value in {"read", "readLine"}) and _value(tokens, index + 1) == "("


def _is_java_output_call(tokens: list[_JavaToken], index: int) -> bool:
    value = tokens[index].value
    if value not in {"print", "println", "printf"} or _value(tokens, index + 1) != "(":
        return False
    context = [_value(tokens, offset) for offset in range(max(0, index - 4), index)]
    return "out" in context or "err" in context


def _is_java_call(tokens: list[_JavaToken], index: int) -> bool:
    value = tokens[index].value
    if not _is_identifier(value) or _value(tokens, index + 1) != "(":
        return False
    if value in _JAVA_CONTROL_WORDS or _value(tokens, index - 1) == "new":
        return False
    return not _is_java_method_declaration(tokens, index)


def _value(tokens: list[_JavaToken], index: int) -> str:
    return tokens[index].value if 0 <= index < len(tokens) else ""


def _next_token(tokens: list[_JavaToken], index: int, value: str) -> int:
    for cursor in range(index + 1, len(tokens)):
        if tokens[cursor].value == value:
            return cursor
        if tokens[cursor].value in {";", "{"}:
            return -1
    return -1


def _matching_token(tokens: list[_JavaToken], index: int, opening: str, closing: str) -> int:
    if _value(tokens, index) != opening:
        return -1
    depth = 0
    for cursor in range(index, len(tokens)):
        if tokens[cursor].value == opening:
            depth += 1
        elif tokens[cursor].value == closing:
            depth -= 1
            if depth == 0:
                return cursor
    return -1


def _balanced_delimiters(code: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for char in code:
        if char in "([{":
            stack.append(char)
        elif char in pairs:
            if not stack or stack.pop() != pairs[char]:
                return False
    return not stack


def _strip_java_comments(code: str) -> str:
    return re.sub(r"//[^\r\n]*|/\*.*?\*/", lambda match: "\n" * match.group(0).count("\n"), code, flags=re.DOTALL)


def _is_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value)) and value not in _JAVA_CONTROL_WORDS


_PYTHON_OPERATOR_KINDS: dict[type[ast.AST], str] = {
    ast.Add: "ARITH_ADD",
    ast.Sub: "ARITH_SUBTRACT",
    ast.Mult: "ARITH_MULTIPLY",
    ast.Div: "ARITH_DIVIDE",
    ast.FloorDiv: "ARITH_DIVIDE",
    ast.Mod: "ARITH_MODULO",
    ast.Eq: "COMPARE_EQUAL",
    ast.NotEq: "COMPARE_NOT_EQUAL",
    ast.Lt: "COMPARE_LESS",
    ast.LtE: "COMPARE_LESS_EQUAL",
    ast.Gt: "COMPARE_GREATER",
    ast.GtE: "COMPARE_GREATER_EQUAL",
}

_PYTHON_UNSUPPORTED_NODES = (
    ast.AsyncFor,
    ast.AsyncFunctionDef,
    ast.Await,
    ast.ClassDef,
    ast.DictComp,
    ast.GeneratorExp,
    ast.Lambda,
    ast.ListComp,
    ast.Match,
    ast.SetComp,
    ast.Try,
    ast.With,
    ast.Yield,
    ast.YieldFrom,
)

_JAVA_TOKEN_PATTERN = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    r"|[A-Za-z_$][A-Za-z0-9_$]*|\d+(?:\.\d+)?"
    r"|==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|%=|->|::"
    r"|[-+*/%=<>!&|^~?:;,.()[\]{}]"
)

_JAVA_OPERATOR_KINDS = {
    "+": "ARITH_ADD",
    "-": "ARITH_SUBTRACT",
    "*": "ARITH_MULTIPLY",
    "/": "ARITH_DIVIDE",
    "%": "ARITH_MODULO",
    "==": "COMPARE_EQUAL",
    "!=": "COMPARE_NOT_EQUAL",
    "<": "COMPARE_LESS",
    "<=": "COMPARE_LESS_EQUAL",
    ">": "COMPARE_GREATER",
    ">=": "COMPARE_GREATER_EQUAL",
    "&&": "LOGIC_AND",
    "||": "LOGIC_OR",
}

_ASSIGNMENT_OPERATORS = {"=", "+=", "-=", "*=", "/=", "%="}
_JAVA_TYPE_TOKENS = {"void", "boolean", "byte", "char", "short", "int", "long", "float", "double"}
_JAVA_CONTROL_WORDS = {
    "catch",
    "class",
    "do",
    "else",
    "for",
    "if",
    "new",
    "return",
    "switch",
    "while",
}
_JAVA_UNSUPPORTED_KEYWORDS = {"catch", "synchronized", "switch", "try", "->"}
