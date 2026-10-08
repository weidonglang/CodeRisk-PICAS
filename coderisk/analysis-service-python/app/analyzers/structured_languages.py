"""C syntax and HTML source-tree analysis. No preprocessing, evaluation or rendering."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import html
from html.parser import HTMLParser
import re

from tree_sitter import Language, Parser
import tree_sitter_c
import tree_sitter_html


@dataclass(frozen=True)
class Lexeme:
    value: str
    line: int
    column: int
    end_line: int


@dataclass
class StructuredSource:
    parsed: bool
    tokens: list[Lexeme]
    nodes: list[tuple[str, int]]
    canonical_tokens: list[str]
    identifiers: list[dict] = field(default_factory=list)
    error: str = ''
    normalization_available: bool = True


@lru_cache(maxsize=2)
def grammar(language: str) -> Language:
    return Language((tree_sitter_c if language == 'c' else tree_sitter_html).language())


def walk(node):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def analyze_source(code: str, language: str) -> StructuredSource:
    data = code.encode('utf-8')
    # Keep parser and tree alive while native Node/Point views are traversed.
    parser = Parser(grammar(language))
    tree = parser.parse(data)
    root = tree.root_node

    def text(node):
        return data[node.start_byte:node.end_byte].decode('utf-8')

    lines = data.split(b'\n')

    def lexeme(node):
        row, byte_column = node.start_point
        return Lexeme(text(node), row + 1, len(lines[row][:byte_column].decode('utf-8')), node.end_point.row + 1)

    # Literals/raw embedded bodies remain indivisible. Comments never shift source offsets.
    atomic = {'string_literal', 'char_literal', 'number_literal', 'system_lib_string', 'preproc_arg'} if language == 'c' else {'quoted_attribute_value', 'attribute_value', 'text', 'raw_text'}
    tokens = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type == 'comment':
            continue
        if node.type in atomic or not node.children:
            if node.end_byte > node.start_byte and text(node).strip():
                tokens.append(lexeme(node))
        else:
            stack.extend(reversed(node.children))
    issues = [n for n in walk(root) if n.is_error or n.is_missing]
    if root.has_error or not tokens:
        detail = ', '.join(f'{n.type} at line {n.start_point.row + 1}' for n in issues[:3])
        return StructuredSource(False, tokens, [], [t.value for t in tokens], error=detail or 'No source tokens')
    if language == 'c':
        nodes = [(n.type, n.start_point.row + 1) for n in walk(root) if n.is_named and n.type != 'comment']
        try:
            canonical, identifiers, available, error = canonical_c(root, data, tokens)
        except RecursionError:
            canonical, identifiers, available, error = [t.value for t in tokens], [], False, 'C binding nesting limit reached'
    else:
        nodes, canonical, available, error = canonical_html(root, text)
        collector = HtmlCanonical(code)
        collector.feed(code)
        collector.close()
        collector.flush()
        canonical = collector.values
        if collector.implicit_nonoptional_close or any(tag not in collector.OPTIONAL_END for tag in collector.stack):
            available, error = False, 'HTML recovered a missing nonoptional closing tag; raw-token fallback'
        identifiers = []
    return StructuredSource(True, tokens, nodes, canonical, identifiers, error, available)


@dataclass
class Binding:
    raw: str
    kind: str
    name: str
    scope: str


@dataclass
class Scope:
    path: str
    parent: Scope | None
    bindings: dict[str, Binding] = field(default_factory=dict)
    children: int = 0

    def child(self):
        self.children += 1
        return Scope(f'{self.path}/S{self.children}', self)

    def declare(self, name, kind):
        if name not in self.bindings:
            index = sum(b.kind == kind for b in self.bindings.values()) + 1
            self.bindings[name] = Binding(name, kind, f'{kind}_{index}', self.path)
        return self.bindings[name]

    def resolve(self, name):
        scope = self
        while scope:
            if name in scope.bindings:
                return scope.bindings[name]
            scope = scope.parent
        return None


def canonical_c(root, data, tokens):
    def text(node):
        return data[node.start_byte:node.end_byte].decode('utf-8')

    all_nodes = list(walk(root))
    # Macros can introduce declarations/uses and conditional branches. Do not invent a binding model.
    unsafe = {'preproc_def', 'preproc_function_def', 'preproc_if', 'preproc_ifdef', 'preproc_call', 'type_definition'}
    if any(n.type in unsafe for n in all_nodes):
        return [t.value for t in tokens], [], False, 'C macros/conditional preprocessing/typedef require raw-token fallback; no expansion is performed'
    if any(n.type == 'storage_class_specifier' and text(n) == 'extern' for n in all_nodes):
        return [t.value for t in tokens], [], False, 'C extern linkage is outside the local binding subset; raw-token fallback'
    for definition in (n for n in all_nodes if n.type == 'function_definition'):
        declarator = definition.child_by_field_name('declarator')
        if declarator and sum(n.type == 'function_declarator' for n in walk(declarator)) > 1:
            return [t.value for t in tokens], [], False, 'C nested function declarators require prototype scopes; raw-token fallback'
        if any(n.type == 'declaration' for n in definition.named_children):
            return [t.value for t in tokens], [], False, 'C old-style parameter declarations require raw-token fallback'

    def declarator_name(node):
        if node is None:
            return None
        if node.type == 'identifier':
            return node
        if node.type == 'parenthesized_declarator' and node.named_children:
            return declarator_name(node.named_children[0])
        return declarator_name(node.child_by_field_name('declarator'))

    global_scope = Scope('ROOT', None)
    overrides = {}

    def bind(node, symbol):
        if node is not None and symbol is not None:
            overrides[node.start_byte] = symbol

    # Function symbols are known to calls occurring before a definition; external library calls are retained.
    for node in root.named_children:
        if node.type in {'function_definition', 'declaration'}:
            for declarator in node.children_by_field_name('declarator'):
                function = next((n for n in walk(declarator) if n.type == 'function_declarator'), None)
                direct = function.child_by_field_name('declarator') if function else None
                if direct and direct.type == 'identifier' and declarator.type != 'init_declarator':
                    name = declarator_name(function)
                    if name:
                        bind(name, global_scope.declare(text(name), 'FUNC'))

    def visit(node, scope):
        if node.type == 'function_definition':
            declarator = node.child_by_field_name('declarator')
            name = declarator_name(declarator)
            bind(name, global_scope.resolve(text(name)) if name else None)
            function_scope = scope.child()
            for part in walk(declarator):
                if part.type == 'parameter_declaration':
                    param = declarator_name(part.child_by_field_name('declarator'))
                    if param:
                        bind(param, function_scope.declare(text(param), 'PARAM'))
            for part in walk(declarator):
                if part.type == 'identifier' and part.start_byte not in overrides:
                    bind(part, function_scope.resolve(text(part)))
            body = node.child_by_field_name('body')
            if body:
                for child in body.named_children:
                    visit(child, function_scope)
            return
        if node.type in {'compound_statement', 'for_statement'}:
            scope = scope.child()
        if node.type == 'declaration':
            for declarator in node.children_by_field_name('declarator'):
                candidate = declarator_name(declarator)
                if candidate:
                    # Function prototypes keep global function bindings; function pointers remain variables.
                    direct = declarator.child_by_field_name('declarator')
                    is_function = declarator.type == 'function_declarator' and direct and direct.type == 'identifier'
                    symbol = global_scope.resolve(text(candidate)) if is_function else scope.declare(text(candidate), 'VAR')
                    bind(candidate, symbol)
                visit(declarator, scope)
            return
        if node.type == 'identifier' and node.start_byte not in overrides:
            # Member names, labels and type names belong to separate namespaces and are preserved.
            parent = node.parent
            if not parent or parent.type not in {'labeled_statement', 'goto_statement', 'enumerator', 'parameter_declaration'}:
                bind(node, scope.resolve(text(node)))
        if node.type in {'parameter_list', 'struct_specifier', 'union_specifier', 'enum_specifier'}:
            return
        for child in node.named_children:
            visit(child, scope)

    visit(root, global_scope)
    canonical, identifiers = [], []
    line_offsets = [0]
    source_lines = data.split(b'\n')
    for index, byte in enumerate(data):
        if byte == 10:
            line_offsets.append(index + 1)
    for position, token in enumerate(tokens):
        line = source_lines[token.line - 1]
        offset = line_offsets[token.line - 1] + len(line.decode('utf-8')[:token.column].encode('utf-8'))
        symbol = overrides.get(offset)
        if symbol is None:
            canonical.append(token.value)
            continue
        scoped = f'{symbol.scope}::{symbol.name}'
        canonical.append(scoped)
        identifiers.append({'rawName': token.value, 'canonicalName': symbol.name,
                            'scopedCanonicalName': scoped, 'scopePath': symbol.scope, 'kind': symbol.kind,
                            'line': token.line, 'column': token.column, 'position': position})
    return canonical, identifiers, True, ''


def canonical_html(root, text):
    nodes, canonical = [], []
    duplicate_attributes = False
    # Iterate source events; attribute sorting affects canonical tokens only, never evidence positions.
    stack = [(root, False, False)]
    while stack:
        node, preserve_space, foreign = stack.pop()
        kind = node.type
        if kind == 'comment':
            continue
        if kind in {'start_tag', 'self_closing_tag', 'end_tag'}:
            tag = next((n for n in node.named_children if n.type == 'tag_name'), None)
            if tag is None:
                continue
            name = text(tag) if foreign else text(tag).lower()
            nodes.append((kind + ':' + name, node.start_point.row + 1))
            canonical.append(('END:' if kind == 'end_tag' else 'START:') + name)
            attrs = []
            for attribute in node.named_children:
                if attribute.type != 'attribute':
                    continue
                children = attribute.named_children
                key = text(children[0]) if foreign else text(children[0]).lower()
                value = text(children[1]) if len(children) > 1 else None
                if value is not None:
                    if value[:1] in {'"', "'"} and value[-1:] == value[:1]:
                        value = value[1:-1]
                    value = html.unescape(value)
                attrs.append((key, value))
            duplicate_attributes |= len({key for key, _ in attrs}) != len(attrs)
            for key, value in sorted(attrs, key=lambda item: item[0]):
                canonical.append('ATTR:' + key + '=' + repr(value))
                nodes.append(('attribute:' + key, node.start_point.row + 1))
            continue
        if kind in {'text', 'raw_text', 'entity'}:
            value = text(node)
            if kind == 'entity':
                value = html.unescape(value)
            if kind == 'text' and not preserve_space:
                value = re.sub(r'\s+', ' ', html.unescape(value)).strip()
            if value:
                canonical.append(('RAW:' if kind == 'raw_text' else 'TEXT:') + value)
                nodes.append((kind, node.start_point.row + 1))
            continue
        if kind == 'doctype':
            canonical.append('DOCTYPE:' + text(node).lower())
            nodes.append(('doctype', node.start_point.row + 1))
            continue
        if kind == 'element':
            start = next((n for n in node.named_children if n.type == 'start_tag'), None)
            tag = next((n for n in start.named_children if n.type == 'tag_name'), None) if start else None
            name = text(tag).lower() if tag else ''
            preserve_space |= name in {'pre', 'textarea'}
            foreign |= name in {'svg', 'math'}
            if preserve_space and start:
                end = next((n for n in reversed(node.named_children) if n.type == 'end_tag'), None)
                canonical.append('PRESERVED_ELEMENT:' + text(node))
                nodes.append(('preserved_element:' + name, node.start_point.row + 1))
                continue
        stack.extend((child, preserve_space, foreign) for child in reversed(node.named_children))
    return nodes, canonical, not duplicate_attributes, 'Duplicate HTML attributes retain raw-token fallback' if duplicate_attributes else ''


class HtmlCanonical(HTMLParser):
    """Preserve source text boundaries that the syntax grammar treats as whitespace extras."""
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
    OPTIONAL_END = {'html', 'head', 'body', 'li', 'dt', 'dd', 'p', 'rt', 'rp', 'optgroup', 'option', 'colgroup', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th'}

    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.values = []
        self.pending = []
        self.stack = []
        self.implicit_nonoptional_close = False

    def flush(self):
        value = ''.join(self.pending)
        if value:
            if not any(tag in {'script', 'style', 'pre', 'textarea', 'svg', 'math'} for tag in self.stack):
                value = re.sub(r'\s+', ' ', value)
            self.values.append('TEXT:' + value)
        self.pending = []

    def handle_starttag(self, tag, attrs):
        self.flush()
        if any(t in {'svg', 'math'} for t in self.stack) or tag in {'svg', 'math'}:
            self.values.append('FOREIGN_START:' + self.get_starttag_text())
        else:
            self.values.append('START:' + tag)
            self.values.extend('ATTR:' + key + '=' + repr(value) for key, value in sorted(attrs, key=lambda item: item[0]))
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        self.flush()
        self.values.append('END:' + tag)
        if tag in self.stack:
            # Optional HTML end tags do not leave a stale whitespace-preserving ancestor.
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            self.implicit_nonoptional_close |= any(t not in self.OPTIONAL_END for t in self.stack[index + 1:])
            self.stack = self.stack[:index]

    def handle_data(self, data):
        self.pending.append(data)

    def handle_entityref(self, name):
        self.pending.append(html.unescape('&' + name + ';'))

    def handle_charref(self, name):
        self.pending.append(html.unescape('&#' + name + ';'))

    def handle_decl(self, decl):
        self.flush()
        self.values.append('DECL:' + decl.lower())
