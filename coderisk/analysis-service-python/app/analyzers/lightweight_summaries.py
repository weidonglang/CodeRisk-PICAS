from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher


SUMMARY_VERSION = 'lightweight-cfg-dfg-summary-v0.2'


@dataclass(frozen=True)
class ControlFlowSummary:
    branch_count: int
    loop_count: int
    max_nesting_depth: int
    condition_pattern_sequence: tuple[str, ...]
    return_count: int
    early_return_count: int
    return_path_summary: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DataFlowSummary:
    input_flow: tuple[str, ...]
    accumulator_update_flow: tuple[str, ...]
    array_index_flow: tuple[str, ...]
    comparison_flow: tuple[str, ...]
    return_dependency: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LightweightSummaries:
    language: str
    parsed: bool
    control: ControlFlowSummary
    data: DataFlowSummary
    warnings: tuple[str, ...] = ()
    error: str = ''


def build_lightweight_summaries(code: str, language: str) -> LightweightSummaries:
    normalized = 'python' if language.lower() == 'py' else language.lower()
    if normalized == 'python':
        return _python_summaries(code)
    if normalized == 'java':
        return _java_summaries(code)
    return LightweightSummaries(
        normalized,
        False,
        _empty_control(),
        _empty_data(),
        error='Lightweight summaries support only Java and Python.',
    )


def control_summary_similarity(left: ControlFlowSummary, right: ControlFlowSummary) -> float:
    components: list[float] = []
    for left_value, right_value in (
        (left.branch_count, right.branch_count),
        (left.loop_count, right.loop_count),
        (left.max_nesting_depth, right.max_nesting_depth),
        (left.return_count, right.return_count),
        (left.early_return_count, right.early_return_count),
    ):
        if left_value or right_value:
            components.append(_count_similarity(left_value, right_value))
    if left.condition_pattern_sequence or right.condition_pattern_sequence:
        components.append(_sequence_similarity(left.condition_pattern_sequence, right.condition_pattern_sequence))
    if left.return_path_summary != 'NO_RETURN' or right.return_path_summary != 'NO_RETURN':
        components.append(1.0 if left.return_path_summary == right.return_path_summary else 0.0)
    return round(sum(components) / len(components), 6) if components else 0.0


def data_flow_summary_similarity(left: DataFlowSummary, right: DataFlowSummary) -> float:
    components: list[float] = []
    for left_values, right_values in (
        (left.input_flow, right.input_flow),
        (left.accumulator_update_flow, right.accumulator_update_flow),
        (left.array_index_flow, right.array_index_flow),
        (left.comparison_flow, right.comparison_flow),
        (left.return_dependency, right.return_dependency),
    ):
        if left_values or right_values:
            components.append(_sequence_similarity(left_values, right_values))
    return round(sum(components) / len(components), 6) if components else 0.0


class _PythonSummaryVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.branch_count = 0
        self.loop_count = 0
        self.control_depth = 0
        self.condition_depth = 0
        self.max_nesting_depth = 0
        self.conditions: list[str] = []
        self.return_count = 0
        self.early_return_count = 0
        self.input_flow: list[str] = []
        self.accumulator_flow: list[str] = []
        self.array_flow: list[str] = []
        self.comparison_flow: list[str] = []
        self.return_dependency: list[str] = []

    def visit_If(self, node: ast.If) -> None:
        self.branch_count += 1
        self._visit_control(node.test, node.body, node.orelse)

    def visit_For(self, node: ast.For) -> None:
        self.loop_count += 1
        self._visit_control(None, node.body, node.orelse)

    def visit_While(self, node: ast.While) -> None:
        self.loop_count += 1
        self._visit_control(node.test, node.body, node.orelse)

    def visit_Compare(self, node: ast.Compare) -> None:
        for operator in node.ops:
            pattern = _PY_COMPARISON_PATTERNS.get(type(operator), 'COMPARE_OTHER')
            if self.condition_depth > 0:
                self.conditions.append(pattern)
            self.comparison_flow.append(pattern)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if _contains_python_input(node.value):
            self.input_flow.append('INPUT_TO_ASSIGN')
        target_names = {name for target in node.targets for name in _python_target_names(target)}
        read_names = {child.id for child in ast.walk(node.value) if isinstance(child, ast.Name)}
        if target_names & read_names and isinstance(node.value, ast.BinOp):
            self.accumulator_flow.append(_python_update_pattern(node.value.op))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None and _contains_python_input(node.value):
            self.input_flow.append('INPUT_TO_ASSIGN')
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.accumulator_flow.append(_python_update_pattern(node.op))
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.array_flow.append('INDEX_WRITE' if isinstance(node.ctx, ast.Store) else 'INDEX_READ')
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if _python_call_name(node.func) == 'print':
            self.input_flow.append('VALUE_TO_OUTPUT')
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        self.return_count += 1
        if self.control_depth > 0:
            self.early_return_count += 1
        self.return_dependency.append(_python_dependency(node.value))
        self.generic_visit(node)

    def _visit_control(self, test: ast.expr | None, body: list[ast.stmt], orelse: list[ast.stmt]) -> None:
        if test is not None:
            self.condition_depth += 1
            self.visit(test)
            self.condition_depth -= 1
        self.control_depth += 1
        self.max_nesting_depth = max(self.max_nesting_depth, self.control_depth)
        for statement in body:
            self.visit(statement)
        for statement in orelse:
            self.visit(statement)
        self.control_depth -= 1


def _python_summaries(code: str) -> LightweightSummaries:
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return LightweightSummaries(
            'python', False, _empty_control(), _empty_data(),
            error=f'Python syntax error at line {error.lineno}: {error.msg}',
        )
    visitor = _PythonSummaryVisitor()
    visitor.visit(tree)
    unsupported = sorted({
        type(node).__name__
        for node in ast.walk(tree)
        if isinstance(node, _PYTHON_UNSUPPORTED)
    })
    return LightweightSummaries(
        'python',
        True,
        ControlFlowSummary(
            visitor.branch_count,
            visitor.loop_count,
            visitor.max_nesting_depth,
            tuple(visitor.conditions),
            visitor.return_count,
            visitor.early_return_count,
            _return_path(visitor.return_count, visitor.early_return_count),
        ),
        DataFlowSummary(
            tuple(visitor.input_flow),
            tuple(visitor.accumulator_flow),
            tuple(visitor.array_flow),
            tuple(visitor.comparison_flow),
            tuple(visitor.return_dependency),
        ),
        tuple(f'Unsupported Python summary construct: {name}' for name in unsupported),
    )


def _java_summaries(code: str) -> LightweightSummaries:
    stripped = _strip_java_comments(code)
    if not _balanced_braces(stripped):
        return LightweightSummaries(
            'java', False, _empty_control(), _empty_data(), error='Java braces are not balanced',
        )
    branch_count, loop_count, depth, return_count, early_returns = _java_control_counts(stripped)
    comparisons = _java_condition_comparisons(stripped)
    input_flow = ['INPUT_TO_ASSIGN' for line in stripped.splitlines() if _JAVA_INPUT_ASSIGN.search(line)]
    input_flow.extend('VALUE_TO_OUTPUT' for _ in _JAVA_OUTPUT.finditer(stripped))
    accumulator_flow = [_java_update_pattern(match.group(1)) for match in _JAVA_AUGMENTED.finditer(stripped)]
    accumulator_flow.extend(_java_update_pattern(match.group(2)) for match in _JAVA_SELF_ASSIGN.finditer(stripped))
    array_flow = [
        'INDEX_WRITE' if _looks_like_java_index_write(stripped, match.end()) else 'INDEX_READ'
        for match in _JAVA_INDEX.finditer(stripped)
    ]
    return_dependencies = tuple(
        _java_dependency(match.group(1)) for match in re.finditer(r'\breturn\s+([^;]+);', stripped)
    )
    unsupported = tuple(
        f'Unsupported Java summary construct: {value}'
        for value in sorted(set(_JAVA_UNSUPPORTED.findall(stripped)))
    )
    return LightweightSummaries(
        'java',
        True,
        ControlFlowSummary(
            branch_count,
            loop_count,
            depth,
            comparisons,
            return_count,
            early_returns,
            _return_path(return_count, early_returns),
        ),
        DataFlowSummary(
            tuple(input_flow),
            tuple(accumulator_flow),
            tuple(array_flow),
            comparisons,
            return_dependencies,
        ),
        unsupported,
    )


def _java_control_counts(code: str) -> tuple[int, int, int, int, int]:
    tokens = re.findall(r'\b(?:if|for|while|do|return)\b|[{}]', code)
    branch_count = sum(token == 'if' for token in tokens)
    loop_count = sum(token in {'for', 'while', 'do'} for token in tokens)
    return_count = sum(token == 'return' for token in tokens)
    early_returns = 0
    pending_control = False
    control_stack: list[bool] = []
    active_depth = 0
    max_depth = 0
    for token in tokens:
        if token in {'if', 'for', 'while', 'do'}:
            pending_control = True
        elif token == 'return':
            if active_depth > 0:
                early_returns += 1
        elif token == '{':
            control_stack.append(pending_control)
            if pending_control:
                active_depth += 1
                max_depth = max(max_depth, active_depth)
            pending_control = False
        elif token == '}':
            if control_stack and control_stack.pop():
                active_depth -= 1
            pending_control = False
    return branch_count, loop_count, max_depth, return_count, early_returns


def _java_condition_comparisons(code: str) -> tuple[str, ...]:
    patterns: list[str] = []
    for condition in re.finditer(r'\b(?:if|while|for)\s*\(([^)]*)\)', code, flags=re.DOTALL):
        patterns.extend(
            _comparison_pattern(match.group(0))
            for match in _COMPARISON_PATTERN.finditer(condition.group(1))
        )
    return tuple(patterns)


def _empty_control() -> ControlFlowSummary:
    return ControlFlowSummary(0, 0, 0, (), 0, 0, 'NO_RETURN')


def _empty_data() -> DataFlowSummary:
    return DataFlowSummary((), (), (), (), ())


def _count_similarity(left: int, right: int) -> float:
    maximum = max(left, right)
    return 1.0 if maximum == 0 else 1.0 - (abs(left - right) / maximum)


def _sequence_similarity(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def _return_path(return_count: int, early_returns: int) -> str:
    if return_count == 0:
        return 'NO_RETURN'
    if early_returns == 0 and return_count == 1:
        return 'SINGLE_TERMINAL_RETURN'
    if early_returns > 0 and return_count == 1:
        return 'SINGLE_GUARDED_RETURN'
    if early_returns > 0:
        return 'MULTI_RETURN_WITH_GUARD'
    return 'MULTI_TERMINAL_RETURN'


def _contains_python_input(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Call) and _python_call_name(child.func) == 'input'
        for child in ast.walk(node)
    )


def _python_call_name(function: ast.expr) -> str:
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return ''


def _python_target_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {name for item in target.elts for name in _python_target_names(item)}
    return set()


def _python_update_pattern(operator: ast.operator) -> str:
    return {
        ast.Add: 'ACCUMULATE_ADD',
        ast.Sub: 'ACCUMULATE_SUBTRACT',
        ast.Mult: 'ACCUMULATE_MULTIPLY',
        ast.Div: 'ACCUMULATE_DIVIDE',
        ast.Mod: 'ACCUMULATE_MODULO',
    }.get(type(operator), 'ACCUMULATE_OTHER')


def _python_dependency(node: ast.expr | None) -> str:
    if node is None:
        return 'RETURN_NONE'
    if isinstance(node, ast.Name):
        return 'RETURN_IDENTIFIER'
    if isinstance(node, ast.Subscript):
        return 'RETURN_INDEX_READ'
    if isinstance(node, ast.BinOp):
        return 'RETURN_ARITHMETIC'
    if isinstance(node, ast.Call):
        return 'RETURN_CALL'
    if isinstance(node, ast.Constant):
        return 'RETURN_CONSTANT'
    return 'RETURN_EXPRESSION'


def _comparison_pattern(operator: str) -> str:
    return {
        '==': 'COMPARE_EQUAL',
        '!=': 'COMPARE_NOT_EQUAL',
        '<': 'COMPARE_LESS',
        '<=': 'COMPARE_LESS_EQUAL',
        '>': 'COMPARE_GREATER',
        '>=': 'COMPARE_GREATER_EQUAL',
    }[operator]


def _java_update_pattern(operator: str) -> str:
    normalized = operator if operator in {'++', '--'} else operator[0]
    return {
        '+': 'ACCUMULATE_ADD',
        '++': 'ACCUMULATE_ADD',
        '-': 'ACCUMULATE_SUBTRACT',
        '--': 'ACCUMULATE_SUBTRACT',
        '*': 'ACCUMULATE_MULTIPLY',
        '/': 'ACCUMULATE_DIVIDE',
        '%': 'ACCUMULATE_MODULO',
    }.get(normalized, 'ACCUMULATE_OTHER')


def _looks_like_java_index_write(code: str, end: int) -> bool:
    return bool(re.match(r'\s*=', code[end:]))


def _java_dependency(expression: str) -> str:
    value = expression.strip()
    if re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*', value):
        return 'RETURN_IDENTIFIER'
    if '[' in value and ']' in value:
        return 'RETURN_INDEX_READ'
    if re.search(r'[+*/%]|(?<![<>=!])-', value):
        return 'RETURN_ARITHMETIC'
    if re.search(r'[A-Za-z_$][A-Za-z0-9_$]*\s*\(', value):
        return 'RETURN_CALL'
    if re.fullmatch(r'(?:\d+(?:\.\d+)?|true|false|null|.*)', value):
        return 'RETURN_CONSTANT'
    return 'RETURN_EXPRESSION'


def _strip_java_comments(code: str) -> str:
    return re.sub(r'//[^\r\n]*|/\*.*?\*/', lambda match: '\n' * match.group(0).count('\n'), code, flags=re.DOTALL)


def _balanced_braces(code: str) -> bool:
    depth = 0
    for character in code:
        if character == '{':
            depth += 1
        elif character == '}':
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


_PY_COMPARISON_PATTERNS: dict[type[ast.cmpop], str] = {
    ast.Eq: 'COMPARE_EQUAL',
    ast.NotEq: 'COMPARE_NOT_EQUAL',
    ast.Lt: 'COMPARE_LESS',
    ast.LtE: 'COMPARE_LESS_EQUAL',
    ast.Gt: 'COMPARE_GREATER',
    ast.GtE: 'COMPARE_GREATER_EQUAL',
}

_PYTHON_UNSUPPORTED = (
    ast.AsyncFor,
    ast.AsyncFunctionDef,
    ast.Await,
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

_COMPARISON_PATTERN = re.compile(r'==|!=|<=|>=|<|>')
_JAVA_INPUT_ASSIGN = re.compile(r'=.*\.(?:next[A-Za-z0-9_]*|read|readLine)\s*\(')
_JAVA_OUTPUT = re.compile(r'\bSystem\s*\.\s*(?:out|err)\s*\.\s*(?:print|println|printf)\s*\(')
_JAVA_AUGMENTED = re.compile(r'(\+\+|--|\+=|-=|\*=|/=|%=)')
_JAVA_SELF_ASSIGN = re.compile(
    r'\b([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*\1\s*([+\-*/%])'
)
_JAVA_INDEX = re.compile(r'\b[A-Za-z_$][A-Za-z0-9_$]*\s*\[[^\]]+\]')
_JAVA_UNSUPPORTED = re.compile(r'\b(?:switch|try|catch|synchronized)\b|->')
