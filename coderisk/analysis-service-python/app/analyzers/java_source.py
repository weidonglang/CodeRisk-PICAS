"""Small lexical helpers; deliberately not a Java grammar or type checker."""
from __future__ import annotations

from collections.abc import Iterable


def mask_comments(code: str) -> tuple[str, str]:
    """Replace comments with spaces, preserving every source offset and CR/LF."""
    output = list(code)
    index = 0
    while index < len(code):
        if code.startswith('//', index) or code.startswith('/*', index):
            block = code.startswith('/*', index)
            end = index + 2
            if block:
                closing = code.find('*/', end)
                end = len(code) if closing < 0 else closing + 2
            else:
                while end < len(code) and code[end] not in '\r\n':
                    end += 1
            for offset in range(index, end):
                if code[offset] not in '\r\n':
                    output[offset] = ' '
            if block and closing < 0:
                return ''.join(output), 'Unterminated Java block comment'
            index = end
        elif code[index] in {'"', "'"}:
            quote = '"""' if code.startswith('"""', index) else code[index]
            index += len(quote)
            while index < len(code):
                if code[index] == '\\':
                    index += 2
                elif code.startswith(quote, index):
                    index += len(quote)
                    break
                elif len(quote) == 1 and code[index] in '\r\n':
                    return ''.join(output), 'Newline in Java string/character literal'
                else:
                    index += 1
            else:
                return ''.join(output), 'Unterminated Java literal'
        else:
            index += 1
    return ''.join(output), ''


def balanced_tokens(values: Iterable[str]) -> bool:
    pairs = {')': '(', ']': '[', '}': '{'}
    stack: list[str] = []
    for value in values:
        if value in {'(', '[', '{'}:
            stack.append(value)
        elif value in pairs and (not stack or stack.pop() != pairs[value]):
            return False
    return not stack
