"""Conservative review context; never changes similarity, labels, or language semantics."""
from __future__ import annotations

import hashlib
import re
import sys

VERSION = 'context-review-v1'
MIN_TEMPLATE_TOKENS = 8
SHORT_TOKENS = 40
NATURAL_SHORT_TOKENS = 120


def language_name(name):
    return {'py': 'python', 'htm': 'html'}.get(name.lower(), name.lower())


def version_key(value, language):
    return re.sub(r'\s+', '', re.sub(r'^(python|java|jdk|html)', '', value.strip().lower())).lstrip('v')


def compatibility(submission, tokens, parsed, normalization_mode):
    language = language_name(submission.language)
    declared = submission.language_version.strip()
    values = [t.value for t in tokens]
    hints, limitations = [], []
    if not parsed:
        limitations.append('STRUCTURE_UNAVAILABLE')
    if normalization_mode == 'lexical-fallback':
        limitations.append('NORMALIZATION_UNAVAILABLE')
    if language == 'python':
        lines = {}
        for token in tokens:
            lines.setdefault(token.line, []).append(token.value)
        if any(v[0] == 'print' and len(v) > 1 and v[1] not in {'(', '=', '.'} for v in lines.values()):
            hints.append('POSSIBLE_PYTHON2_PRINT_STATEMENT')
        if any(v == 'raw_input' and i + 1 < len(values) and values[i + 1] == '(' for i, v in enumerate(values)):
            hints.append('RAW_INPUT_NAME_REQUIRES_VERSION_REVIEW')
        if ':=' in values:
            hints.append('ASSIGNMENT_EXPRESSION_SYNTAX')
        key = version_key(declared, language)
        if re.match(r'^2(?:\.|$)', key):
            limitations.append('DECLARED_PYTHON2_NOT_VALIDATED_BY_PYTHON3_PARSER')
        if '/' in values and (re.match(r'^2(?:\.|$)', key) or 'POSSIBLE_PYTHON2_PRINT_STATEMENT' in hints):
            limitations.append('PYTHON_DIVISION_REQUIRES_VERSION_SEMANTICS_REVIEW')
        match = re.fullmatch(r'3\.(\d+)(?:\.\d+)?', key)
        if match and int(match[1]) > sys.version_info.minor:
            limitations.append('DECLARED_VERSION_NEWER_THAN_PARSER_RUNTIME')
    elif language == 'java':
        if any(v.startswith('"""') for v in values):
            hints.append('TEXT_BLOCK_SYNTAX')
        if '->' in values:
            hints.append('ARROW_SYNTAX_VERSION_NOT_INFERRED')
    elif language == 'c':
        if any(values[i:i + 3] == ['std', ':', ':'] for i in range(max(0, len(values) - 2))) or any(values[i:i + 2] == ['using', 'namespace'] for i in range(max(0, len(values) - 1))):
            limitations.append('CPP_SYNTAX_HINT_IN_C_SUBMISSION')
    return {'language': language, 'declaredVersion': declared or 'UNKNOWN', 'versionProvenance': 'SUBMITTER_DECLARATION_UNVERIFIED' if declared else 'UNKNOWN',
            'syntaxParsed': parsed, 'normalizationMode': normalization_mode, 'syntaxHints': hints,
            'limitations': limitations, 'languageVersionValidated': False,
            'parserRuntime': f'Python {sys.version_info.major}.{sys.version_info.minor}' if language == 'python' else 'grammar/subset; no compiler validation',
            'sourceConverted': False}


def exact_spans(values, pattern):
    """Linear KMP exact token matching, including repeated occurrences."""
    if not pattern:
        return []
    prefix, matched = [0] * len(pattern), 0
    for i in range(1, len(pattern)):
        while matched and pattern[i] != pattern[matched]:
            matched = prefix[matched - 1]
        if pattern[i] == pattern[matched]:
            matched += 1
        prefix[i] = matched
    spans, matched = [], 0
    for i, value in enumerate(values):
        while matched and value != pattern[matched]:
            matched = prefix[matched - 1]
        if value == pattern[matched]:
            matched += 1
        if matched == len(pattern):
            spans.append((i + 1 - matched, i + 1))
            matched = prefix[matched - 1]
    return spans


def template_context(question, submissions, token_lists, tokenize):
    language = language_name(question.starter_language)
    code = question.starter_code
    registered = bool(code.strip())
    marker = {'python': r'\# CODERISK_STUDENT_CODE', 'java': r'/\* CODERISK_STUDENT_CODE \*/',
              'c': r'/\* CODERISK_STUDENT_CODE \*/', 'html': r'<!-- CODERISK_STUDENT_CODE -->'}.get(language)
    # Only a standalone comment line is a hole. Marker text in a literal is not removed.
    chunks = [code]
    if registered and marker:
        original_tokens = tokenize(code, language)
        matches = []
        for match in re.finditer(r'(?m)^[ \t]*' + marker + r'[ \t]*\r?$', code):
            line = code.count('\n', 0, match.start()) + 1
            if not any(t.line <= line <= (t.end_line or t.line) for t in original_tokens):
                matches.append(match)
        start, chunks = 0, []
        for match in matches:
            chunks.append(code[start:match.start()])
            start = match.end()
        chunks.append(code[start:])
    patterns = [[t.value for t in tokenize(chunk, language)] for chunk in chunks] if registered else []
    eligible = [p for p in patterns if len(p) >= MIN_TEMPLATE_TOKENS]
    context = {'registered': registered, 'language': language or 'UNKNOWN', 'sourceReference': question.starter_source,
               'sourceProvenance': 'USER_REGISTERED_NOT_INDEPENDENTLY_VERIFIED', 'minimumSegmentTokens': MIN_TEMPLATE_TOKENS,
               'templateSha256': hashlib.sha256(code.encode()).hexdigest() if registered else None,
               'matchingPolicy': 'EXACT_RAW_TOKEN_SEGMENTS_ONLY', 'includedInProductionScore': False,
               'eligibleSegmentCount': len(eligible), 'shortSegmentsIgnored': len(patterns) - len(eligible) if registered else 0}
    residuals = []
    for side, submission, tokens in zip(('A', 'B'), submissions, token_lists):
        mask, fragments = set(), []
        applicable = registered and language_name(submission.language) == language
        if applicable:
            values = [t.value for t in tokens]
            for index, pattern in enumerate(eligible):
                for start, end in exact_spans(values, pattern):
                    mask.update(range(start, end))
                    if len(fragments) < 20:
                        fragments.append({'segment': index, 'startLine': tokens[start].line, 'endLine': tokens[end-1].end_line or tokens[end-1].line,
                                          'startToken': start, 'endTokenExclusive': end})
        residuals.append([t for i, t in enumerate(tokens) if i not in mask])
        context['submission' + side] = {'applicable': applicable, 'tokenCount': len(tokens), 'matchedTemplateTokens': len(mask),
            'effectiveTokenCount': len(tokens) - len(mask), 'templateCoverage': round(len(mask) / len(tokens), 6) if tokens else 0.0,
            'fragments': fragments, 'fragmentDisplayLimit': 20}
    left, right = ({t.value for t in items} for items in residuals)
    context['nonTemplateTokenSetSimilarity'] = round(len(left & right) / len(left | right), 6) if left and right else None
    context['diagnosticRepresentation'] = 'RAW_TOKEN_VALUE_SET_NO_ADJACENCY_NOT_PRODUCTION_NGRAM_SCORE'
    return context, residuals


def assessment(compatibilities, template, natural_risk, cross_language):
    a, b = (template['submission' + side] for side in ('A', 'B'))
    reasons = []
    versions = [r['declaredVersion'] for r in compatibilities]
    same_language = compatibilities[0]['language'] == compatibilities[1]['language']
    differing_versions = same_language and all(v != 'UNKNOWN' for v in versions) and version_key(versions[0], compatibilities[0]['language']) != version_key(versions[1], compatibilities[1]['language'])
    if differing_versions:
        reasons.append('DECLARED_LANGUAGE_VERSIONS_DIFFER')
    if any(r['limitations'] or r['syntaxHints'] for r in compatibilities):
        reasons.append('PARSER_OR_VERSION_LIMITATIONS')
    if cross_language:
        reasons.append('CROSS_LANGUAGE_EXPERIMENTAL')
    minimum = min(a['effectiveTokenCount'], b['effectiveTokenCount'])
    natural = natural_risk is not None and natural_risk >= .60
    insufficient = minimum <= SHORT_TOKENS
    if minimum == 0:
        reasons.append('NO_NON_TEMPLATE_CONTENT' if a['matchedTemplateTokens'] or b['matchedTemplateTokens'] else 'EMPTY_OR_COMMENT_ONLY_SOURCE')
    elif insufficient:
        reasons.append('SHORT_EFFECTIVE_CODE')
    if natural:
        reasons.append('HEURISTIC_NATURAL_SIMILARITY_RISK')
        if minimum <= NATURAL_SHORT_TOKENS:
            insufficient = True
            reasons.append('LIMITED_CODE_UNDER_CONCENTRATED_SOLUTION_SPACE')
    if max(a['templateCoverage'], b['templateCoverage']) >= .5:
        reasons.append('SHARED_TEMPLATE_DOMINATES')
    elif a['matchedTemplateTokens'] or b['matchedTemplateTokens']:
        reasons.append('REGISTERED_SHARED_TEMPLATE_MATCH')
    status = 'INSUFFICIENT_DISTINGUISHING_EVIDENCE' if insufficient else 'CONTEXT_REVIEW_REQUIRED' if reasons else 'SIMILARITY_SIGNALS_ONLY'
    message = ('可区分代码依据不足；短代码、共同模板或题目约束可能造成自然相似，不能据分数认定关系。' if insufficient else
               '需要结合语言版本、解析范围与共同题目背景复核；相似分数不能证明独立或派生关系。' if reasons else
               '当前仅提供相似信号；仍须核验来源和独立创作或派生依据。')
    return {'policyVersion': VERSION, 'status': status, 'message': message, 'reasons': reasons,
            'shortCodeTokenLimit': SHORT_TOKENS, 'naturalRiskShortCodeTokenLimit': NATURAL_SHORT_TOKENS,
            'naturalRiskTrigger': .60, 'policyCalibrated': False, 'includedInProductionScore': False,
            'templateDominanceTrigger': .50,
            'relationshipDetermined': False, 'declaredVersionDifference': differing_versions}
