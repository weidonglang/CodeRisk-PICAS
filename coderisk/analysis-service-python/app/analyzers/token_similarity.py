from __future__ import annotations

import ast
import io
import keyword
import math
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path

from app.analyzers.java_source import balanced_tokens, mask_comments
from app.analyzers.review_context import compatibility, template_context, assessment

from app.analyzers.canonicalization import (
    IdentifierMappingAnalysis,
    build_identifier_mapping,
    canonicalize_code,
)
from app.analyzers.normalized_ir import IR_VERSION, compare_normalized_ir
from app.analyzers.lightweight_summaries import (
    SUMMARY_VERSION,
    build_lightweight_summaries,
    control_summary_similarity,
    data_flow_summary_similarity,
)
from app.analyzers.problem_profile import (
    FORMULA_VERSION,
    MARGIN_SCALE,
    build_problem_profile,
    calibrated_risk_score,
    calculate_dynamic_threshold,
    risk_level_from_margin,
    ThresholdResult,
)
from app.schemas.analyze_schema import (
    AnalyzeMockRequest,
    AnalyzeMockResult,
    EvidenceResult,
    MetricResult,
    SubmissionPayload,
)

JAVA_TOKEN_PATTERN = re.compile(
    r'"""(?:\\[\s\S]|(?!""")[^\\])*"""'
    r'|"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
    r"|[A-Za-z_$][A-Za-z0-9_$]*"
    r"|\d+(?:\.\d+)?"
    r"|==|!=|<=|>=|&&|\|\||\+\+|--|->|::"
    r"|[-+*/%=<>!&|^~?:;,.()[\]{}]"
)

MAX_EVIDENCE_FRAGMENTS = 5

# "PICAS_CROSSLANG" keeps experimental IR outside the production score.


@dataclass(frozen=True)
class TokenItem:
    value: str
    line: int
    column: int
    end_line: int | None = None


@dataclass(frozen=True)
class AstNodeItem:
    value: str
    line: int


@dataclass(frozen=True)
class AstAnalysis:
    parsed: bool
    nodes: list[AstNodeItem]
    error: str = ""


def analyze_token_pair(request: AnalyzeMockRequest) -> AnalyzeMockResult:
    languages = {'python' if s.language.lower() == 'py' else 'html' if s.language.lower() == 'htm' else s.language.lower()
                 for s in (request.submission_a, request.submission_b)}
    if len(languages) > 1 and languages & {'c', 'html'}:
        raise ValueError('C and HTML require same-language pairs; cross-language support remains limited to Java/Python')
    code_a = _read_submission_code(request.submission_a)
    code_b = _read_submission_code(request.submission_b)
    token_items_a = tokenize_code_with_locations(code_a, request.submission_a.language)
    token_items_b = tokenize_code_with_locations(code_b, request.submission_b.language)
    tokens_a = [item.value for item in token_items_a]
    tokens_b = [item.value for item in token_items_b]

    fingerprints_a = _fingerprints(tokens_a)
    fingerprints_b = _fingerprints(tokens_b)
    token_similarity = _jaccard(fingerprints_a, fingerprints_b) if tokens_a and tokens_b else 0.0
    html_pair = all(s.language.lower() in {'html', 'htm'} for s in (request.submission_a, request.submission_b))
    problem_profile = None
    if html_pair:
        try:
            fixed = float(request.config.get('htmlThreshold', 0.85))
        except (TypeError, ValueError) as error:
            raise ValueError('htmlThreshold must be a finite value in [0, 1]') from error
        if not math.isfinite(fixed) or not 0 <= fixed <= 1:
            raise ValueError('htmlThreshold must be a finite value in [0, 1]')
        threshold_result = ThresholdResult(fixed, fixed, 0, 0, 0, 0, 0,
            'Experimental HTML fixed threshold; algorithm-problem dynamic adjustments do not apply. Not calibrated on labelled HTML data.')
        dynamic_threshold = fixed
    else:
        problem_profile = build_problem_profile(request.question, request.config)
        threshold_result = calculate_dynamic_threshold(problem_profile, request.config)
        dynamic_threshold = threshold_result.dynamic_threshold

    ast_a = parse_ast_nodes(code_a, request.submission_a.language)
    ast_b = parse_ast_nodes(code_b, request.submission_b.language)
    ast_similarity = _sequence_similarity([node.value for node in ast_a.nodes], [node.value for node in ast_b.nodes]) if ast_a.parsed and ast_b.parsed and tokens_a and tokens_b else 0.0

    ast_enabled = bool(ast_a.parsed and ast_b.parsed and tokens_a and tokens_b)
    canonical_a = canonicalize_code(code_a, request.submission_a.language, token_items_a)
    canonical_b = canonicalize_code(code_b, request.submission_b.language, token_items_b)
    canonical_enabled = ast_enabled and not (
        canonical_a.mode == "lexical-fallback" or canonical_b.mode == "lexical-fallback"
    )
    canonical_similarity = (
        _sequence_similarity(canonical_a.tokens, canonical_b.tokens) if canonical_enabled else 0.0
    )
    identifier_mapping = (
        build_identifier_mapping(canonical_a, canonical_b)
        if canonical_enabled
        else IdentifierMappingAnalysis([], 0.0, 0.0, 0.0)
    )
    identifier_mapping_similarity = identifier_mapping.similarity
    analysis_mode = str(request.config.get('mode', 'PICAS_STANDARD')).strip().upper()
    ir_comparison = (
        compare_normalized_ir(
            code_a,
            request.submission_a.language,
            code_b,
            request.submission_b.language,
        )
        if analysis_mode == 'PICAS_CROSSLANG'
        else None
    )
    summary_a = build_lightweight_summaries(code_a, request.submission_a.language) if ir_comparison else None
    summary_b = build_lightweight_summaries(code_b, request.submission_b.language) if ir_comparison else None
    summaries_comparable = bool(
        summary_a and summary_b and summary_a.parsed and summary_b.parsed
        and {summary_a.language, summary_b.language} == {'java', 'python'}
    )
    control_summary_score = (
        control_summary_similarity(summary_a.control, summary_b.control) if summaries_comparable else 0.0
    )
    data_flow_summary_score = (
        data_flow_summary_similarity(summary_a.data, summary_b.data) if summaries_comparable else 0.0
    )

    weighted_similarity = _weighted_similarity(
        token_similarity,
        ast_similarity,
        canonical_similarity,
        identifier_mapping_similarity,
        ast_enabled,
        canonical_enabled,
    )
    if html_pair and canonical_enabled:
        weighted_similarity = 0.25 * token_similarity + 0.30 * ast_similarity + 0.45 * canonical_similarity
    risk_margin = round(weighted_similarity - dynamic_threshold, 6)
    risk_level = risk_level_from_margin(risk_margin)
    calibrated_score = calibrated_risk_score(risk_margin, MARGIN_SCALE)

    overlap_count = len(fingerprints_a & fingerprints_b)
    fragments = _overlap_fragments(token_items_a, token_items_b)
    evidence = [
        EvidenceResult(
            evidenceType="TOKEN_MATCH",
            similarityScore=round(token_similarity, 6),
            description="Token fingerprint overlap from the V1 token analysis pipeline.",
            metadata={
                "tokenCountA": len(tokens_a),
                "tokenCountB": len(tokens_b),
                "fingerprintCountA": len(fingerprints_a),
                "fingerprintCountB": len(fingerprints_b),
                "overlapCount": overlap_count,
                "ngramSize": _ngram_size(min(len(tokens_a), len(tokens_b))),
                "fragments": fragments,
                "astEnabled": ast_enabled,
            },
        )
    ]
    if ast_enabled:
        evidence.append(
            EvidenceResult(
                evidenceType="AST_STRUCTURE_MATCH",
                similarityScore=round(ast_similarity, 6),
                description=("HTML source tag/attribute tree sequence similarity; not a rendered browser DOM." if html_pair else
                             "Basic AST node-type sequence similarity. Does not perform subtree, CFG, DFG, or IR matching."),
                metadata={
                    "nodeCountA": len(ast_a.nodes),
                    "nodeCountB": len(ast_b.nodes),
                    "fragments": _overlap_ast_fragments(ast_a.nodes, ast_b.nodes),
                    "parser": _parser_name(request.submission_a.language),
                    "parserA": _parser_name(request.submission_a.language),
                    "parserB": _parser_name(request.submission_b.language),
                },
            )
        )
    else:
        evidence.append(
            EvidenceResult(
                evidenceType="PARSER_WARNING",
                similarityScore=0.0,
                description="Parsing failed for at least one submission; analysis fell back to token-only signals.",
                metadata={
                    "parserStatusA": "PARSED" if ast_a.parsed else "FAILED",
                    "parserStatusB": "PARSED" if ast_b.parsed else "FAILED",
                    "parserErrorA": ast_a.error,
                    "parserErrorB": ast_b.error,
                    "astEnabled": False,
                },
            )
        )
    if ast_enabled and not canonical_enabled:
        evidence.append(EvidenceResult(
            evidenceType="PARSER_WARNING",
            similarityScore=0.0,
            description="Scope normalization is unavailable; weighted analysis fell back to raw tokens.",
            metadata={"normalizationModeA": canonical_a.mode, "normalizationModeB": canonical_b.mode,
                      "normalizationReasonA": ast_a.error, "normalizationReasonB": ast_b.error},
        ))
    if canonical_enabled and canonical_similarity > 0:
        evidence.append(
            EvidenceResult(
                evidenceType="CANONICAL_TOKEN_MATCH",
                similarityScore=round(canonical_similarity, 6),
                description="Canonical token similarity after identifier normalization.",
                metadata={
                    "rawTokenSimilarity": round(token_similarity, 6),
                    "canonicalTokenSimilarity": round(canonical_similarity, 6),
                    "identifierCountA": len(canonical_a.identifiers),
                    "identifierCountB": len(canonical_b.identifiers),
                    "normalizationModeA": canonical_a.mode,
                    "normalizationModeB": canonical_b.mode,
                },
            )
        )
    if canonical_enabled and identifier_mapping.mappings:
        evidence.append(
            EvidenceResult(
                evidenceType="IDENTIFIER_MAPPING",
                similarityScore=round(identifier_mapping_similarity, 6),
                description="Scope-aware identifier mapping for variables, parameters, functions, and classes; supports manual review only.",
                metadata={
                    "mappings": identifier_mapping.mappings,
                    "mappingCount": len(identifier_mapping.mappings),
                    "mappingCoverage": identifier_mapping.coverage,
                    "mappingConsistency": identifier_mapping.consistency,
                    "normalizationModeA": canonical_a.mode,
                    "normalizationModeB": canonical_b.mode,
                },
            )
        )

    if html_pair:
        evidence.append(EvidenceResult(
            evidenceType='REVIEW_NOTE', similarityScore=0.0,
            description='Experimental HTML source-tree similarity; common page templates need manual review. Embedded JavaScript/CSS are opaque text. No page is rendered or executed.',
            metadata={'language': 'html', 'thresholdPolicy': 'FIXED_UNCALIBRATED',
                      'identifierMappingApplicable': False, 'embeddedCodeAnalysis': 'opaque-text'}))
    elif 'c' in languages:
        evidence.append(EvidenceResult(
            evidenceType='REVIEW_NOTE', similarityScore=0.0,
            description='C uses a Tree-sitter syntax tree and conservative local bindings. No compilation, macro expansion, type checking or execution is performed.',
            metadata={'language': 'c', 'normalizationModeA': canonical_a.mode, 'normalizationModeB': canonical_b.mode}))

    if ir_comparison is not None:
        ir_metadata = {
            'experimental': True,
            'irVersion': IR_VERSION,
            'includedInWeightedScore': False,
            'coverageA': ir_comparison.left.coverage,
            'coverageB': ir_comparison.right.coverage,
            'supportedA': ir_comparison.left.supported,
            'supportedB': ir_comparison.right.supported,
            'irSequenceA': [node.kind for node in ir_comparison.left.nodes],
            'irSequenceB': [node.kind for node in ir_comparison.right.nodes],
            'warningsA': ir_comparison.left.warnings,
            'warningsB': ir_comparison.right.warnings,
            'fragments': ir_comparison.fragments,
        }
        if ir_comparison.comparable and ir_comparison.fragments:
            evidence.append(EvidenceResult(
                evidenceType='CROSSLANG_IR_MATCH',
                similarityScore=ir_comparison.similarity,
                description='Experimental Java-Python normalized IR similarity; zero production weight and no semantic-equivalence claim.',
                metadata=ir_metadata,
            ))
        else:
            warning_type = 'PARSER_WARNING' if not ir_comparison.left.parsed or not ir_comparison.right.parsed else 'REVIEW_NOTE'
            evidence.append(EvidenceResult(
                evidenceType=warning_type,
                similarityScore=0.0,
                description='Experimental cross-language IR unavailable; no IR evidence was generated. ' + ir_comparison.reason,
                metadata={**ir_metadata, 'irEvidenceGenerated': False, 'reason': ir_comparison.reason},
            ))

    if summaries_comparable and summary_a is not None and summary_b is not None:
        summary_metadata = {
            'experimental': True,
            'summaryVersion': SUMMARY_VERSION,
            'includedInWeightedScore': False,
            'warningsA': list(summary_a.warnings),
            'warningsB': list(summary_b.warnings),
        }
        evidence.append(EvidenceResult(
            evidenceType='CONTROL_STRUCTURE_MATCH',
            similarityScore=control_summary_score,
            description='Experimental lightweight control-flow summary similarity; no CFG graph is constructed.',
            metadata={
                **summary_metadata,
                'summaryKind': 'LIGHTWEIGHT_CONTROL_FLOW_SUMMARY',
                'controlSummaryA': summary_a.control.as_dict(),
                'controlSummaryB': summary_b.control.as_dict(),
            },
        ))
        evidence.append(EvidenceResult(
            evidenceType='OPERATION_SEQUENCE_MATCH',
            similarityScore=data_flow_summary_score,
            description='Experimental lightweight data-flow summary similarity; no DFG graph is constructed.',
            metadata={
                **summary_metadata,
                'summaryKind': 'LIGHTWEIGHT_DATA_FLOW_SUMMARY',
                'dataFlowSummaryA': summary_a.data.as_dict(),
                'dataFlowSummaryB': summary_b.data.as_dict(),
            },
        ))

    ir_metrics: list[MetricResult] = []
    if ir_comparison is not None:
        available = ir_comparison.comparable
        ir_metrics.append(MetricResult(
            name='CROSSLANG_IR_SIMILARITY',
            value=ir_comparison.similarity if available else 0.0,
            weight=0.0,
            explanation=(
                f'Experimental {IR_VERSION}; zero production weight and excluded from PICAS_STANDARD.'
                if available
                else f'Experimental {IR_VERSION} unavailable: {ir_comparison.reason}'
            ),
        ))
        ir_metrics.extend([
            MetricResult(
                name='CROSSLANG_CONTROL_SUMMARY_SIMILARITY',
                value=control_summary_score,
                weight=0.0,
                explanation=(
                    f'Experimental {SUMMARY_VERSION}; lightweight counts and sequences only, no CFG graph.'
                    if summaries_comparable
                    else f'Experimental {SUMMARY_VERSION} unavailable because a summary parser failed.'
                ),
            ),
            MetricResult(
                name='CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY',
                value=data_flow_summary_score,
                weight=0.0,
                explanation=(
                    f'Experimental {SUMMARY_VERSION}; lightweight dependency patterns only, no DFG graph.'
                    if summaries_comparable
                    else f'Experimental {SUMMARY_VERSION} unavailable because a summary parser failed.'
                ),
            ),
        ])

    compatibilities = [compatibility(submission, tokens, parsed.parsed, canonical.mode)
                      for submission, tokens, parsed, canonical in zip(
                          (request.submission_a, request.submission_b), (token_items_a, token_items_b),
                          (ast_a, ast_b), (canonical_a, canonical_b))]
    shared_template, _ = template_context(request.question, (request.submission_a, request.submission_b),
                                         (token_items_a, token_items_b), tokenize_code_with_locations)
    review = assessment(compatibilities, shared_template, None if html_pair else problem_profile.natural_similarity_risk,
                        len(languages) > 1)
    evidence.extend([
        EvidenceResult(evidenceType='REVIEW_NOTE', similarityScore=0.0,
                       description='Language versions are declarations, not compiler-validated facts; syntax differences are not converted automatically.',
                       metadata={'category': 'LANGUAGE_COMPATIBILITY', 'submissionA': compatibilities[0], 'submissionB': compatibilities[1]}),
        EvidenceResult(evidenceType='REVIEW_NOTE', similarityScore=0.0, description=review['message'],
                       metadata={'category': 'REVIEW_ASSESSMENT', **review}),
        EvidenceResult(evidenceType='REVIEW_NOTE', similarityScore=0.0,
                       description='Registered shared template matches are review context only; effective token counts do not prove independent creation.',
                       metadata={'category': 'SHARED_TEMPLATE_CONTEXT', **shared_template}),
    ])
    result = AnalyzeMockResult(
        taskId=request.task_id,
        submissionAId=request.submission_a.id,
        submissionBId=request.submission_b.id,
        tokenSimilarity=round(token_similarity, 6),
        astSimilarity=round(ast_similarity, 6),
        canonicalTokenSimilarity=round(canonical_similarity, 6),
        identifierMappingSimilarity=round(identifier_mapping_similarity, 6),
        weightedSimilarityScore=round(weighted_similarity, 6),
        dynamicThreshold=dynamic_threshold,
        riskMargin=risk_margin,
        calibratedRiskScore=calibrated_score,
        exceedThreshold=weighted_similarity >= dynamic_threshold,
        marginScale=MARGIN_SCALE,
        formulaVersion='HTML_STRUCTURE_FIXED_V1' if html_pair else FORMULA_VERSION,
        riskLevel=risk_level,
        problemProfile=({'featureVersion': 'html-markup-profile-v1', 'domain': 'html', 'confidence': 0.0,
                         'explanation': {'note': 'No calibrated HTML task complexity model is available.'}}
                        if html_pair else problem_profile.as_dict()),
        thresholdAdjustment={**threshold_result.as_dict(),
                             **({'formulaVersion': 'HTML_STRUCTURE_FIXED_V1', 'policy': 'FIXED_UNCALIBRATED'} if html_pair else {})},
        reasonSummary=_reason_summary(
            risk_level,
            weighted_similarity >= dynamic_threshold,
            analysis_mode == 'PICAS_CROSSLANG',
        ),
        isMock=False,
        metrics=[
            MetricResult(
                name="TOKEN_SIMILARITY",
                value=round(token_similarity, 6),
                weight=(0.25 if html_pair else 0.20) if canonical_enabled else 1.0,
                explanation="Raw token n-gram Jaccard similarity.",
            ),
            MetricResult(
                name="AST_SIMILARITY",
                value=round(ast_similarity, 6),
                weight=(0.30 if html_pair else 0.20) if canonical_enabled else 0.0,
                explanation="Source-tree structure similarity (DOM tags for HTML). Falls back to 0 when parsing fails.",
            ),
            MetricResult(
                name="CANONICAL_TOKEN_SIMILARITY",
                value=round(canonical_similarity, 6),
                weight=0.45 if canonical_enabled else 0.0,
                explanation=(
                    ("HTML tag/attribute canonicalization with text, class/id and resource values preserved."
                     if html_pair else "Token similarity after scope-aware identifier normalization.")
                    if canonical_enabled
                    else "Unavailable because parsing or scope normalization failed; no canonical evidence was generated."
                ),
            ),
            MetricResult(
                name="IDENTIFIER_MAPPING_SIMILARITY",
                value=round(identifier_mapping_similarity, 6),
                weight=0.15 if canonical_enabled and not html_pair else 0.0,
                explanation=(
                    "Coverage and consistency of aligned canonical identifiers."
                    if canonical_enabled
                    else "Unavailable because parsing or scope normalization failed; no identifier mapping was generated."
                ),
            ),
            *ir_metrics,
        ],
        evidence=evidence,
    )
    return result


def tokenize_code(code: str, language: str) -> list[str]:
    return [item.value for item in tokenize_code_with_locations(code, language)]


def tokenize_code_with_locations(code: str, language: str) -> list[TokenItem]:
    normalized_language = language.lower()
    if normalized_language in {"python", "py"}:
        return _tokenize_python(code)
    if normalized_language == "java":
        return _tokenize_java(code)
    if normalized_language in {'c', 'html', 'htm'}:
        from app.analyzers.structured_languages import analyze_source
        source = analyze_source(code, 'html' if normalized_language == 'htm' else normalized_language)
        return [TokenItem(token.value, token.line, token.column, token.end_line) for token in source.tokens]
    return _tokenize_generic(code)


def parse_ast_nodes(code: str, language: str) -> AstAnalysis:
    normalized_language = language.lower()
    if normalized_language in {"python", "py"}:
        return _parse_python_ast(code)
    if normalized_language == "java":
        return _parse_java_structure(code)
    if normalized_language in {'c', 'html', 'htm'}:
        from app.analyzers.structured_languages import analyze_source
        source = analyze_source(code, 'html' if normalized_language == 'htm' else normalized_language)
        return AstAnalysis(source.parsed, [AstNodeItem(value, line) for value, line in source.nodes], source.error)
    return AstAnalysis(False, [], f"AST parser not available for language: {language}")


def _parser_name(language: str) -> str:
    return {'python': 'python-ast', 'py': 'python-ast', 'java': 'minimal-java-structure',
            'c': 'tree-sitter-c', 'html': 'tree-sitter-html', 'htm': 'tree-sitter-html'}.get(language.lower(), 'generic-token-only')


def _read_submission_code(submission: SubmissionPayload) -> str:
    if submission.code:
        return submission.code
    if not submission.raw_code_path:
        return ""
    return Path(submission.raw_code_path).read_text(encoding="utf-8", errors="replace")


def _parse_python_ast(code: str) -> AstAnalysis:
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return AstAnalysis(False, [], f"Python syntax error at line {error.lineno}: {error.msg}")
    nodes: list[AstNodeItem] = []

    def visit(node: ast.AST, parent_line: int = 1) -> None:
        line = int(getattr(node, "lineno", parent_line) or parent_line)
        nodes.append(AstNodeItem(type(node).__name__, line))
        for child in ast.iter_child_nodes(node):
            visit(child, line)

    visit(tree)
    return AstAnalysis(True, nodes)


def _parse_java_structure(code: str) -> AstAnalysis:
    stripped, error = mask_comments(code)
    if error:
        return AstAnalysis(False, [], error)
    tokens = _regex_tokenize_with_lines(stripped)
    if not balanced_tokens(token.value for token in tokens):
        return AstAnalysis(False, [], "Java delimiters are not balanced")
    if not tokens:
        return AstAnalysis(False, [], "No Java tokens found")

    nodes: list[AstNodeItem] = [AstNodeItem("CompilationUnit", 1)]
    raw_values = [item.value for item in tokens]
    for index, item in enumerate(tokens):
        value = item.value
        previous = raw_values[index - 1] if index > 0 else ""
        next_value = raw_values[index + 1] if index + 1 < len(raw_values) else ""
        if value == "class":
            nodes.append(AstNodeItem("ClassDeclaration", item.line))
        elif value in {"if", "else", "switch"}:
            nodes.append(AstNodeItem("BranchStatement", item.line))
        elif value in {"for", "while", "do"}:
            nodes.append(AstNodeItem("LoopStatement", item.line))
        elif value == "return":
            nodes.append(AstNodeItem("ReturnStatement", item.line))
        elif value == "try":
            nodes.append(AstNodeItem("TryStatement", item.line))
        elif value == "catch":
            nodes.append(AstNodeItem("CatchClause", item.line))
        elif value == "=":
            nodes.append(AstNodeItem("Assignment", item.line))
        elif value in {"+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">="}:
            nodes.append(AstNodeItem("Expression", item.line))
        elif _is_identifier(value, "java") and next_value == "(" and previous not in {"if", "for", "while", "switch", "catch", "new", "."}:
            nodes.append(AstNodeItem("MethodDeclarationOrCall", item.line))
        elif value == "{":
            nodes.append(AstNodeItem("Block", item.line))

    if len(nodes) == 1:
        return AstAnalysis(False, [], "No Java structural nodes found")
    return AstAnalysis(True, nodes)


def _tokenize_python(code: str) -> list[TokenItem]:
    tokens: list[TokenItem] = []
    ignored = {
        tokenize.ENCODING,
        tokenize.ENDMARKER,
        tokenize.NEWLINE,
        tokenize.NL,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.COMMENT,
    }
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type in ignored:
                continue
            tokens.append(TokenItem(token.string, max(1, token.start[0]), max(0, token.start[1]), max(1, token.end[0])))
    except (tokenize.TokenError, IndentationError):
        return _tokenize_generic(code)
    return tokens


def _tokenize_java(code: str) -> list[TokenItem]:
    return _regex_tokenize_with_lines(_strip_java_comments(code))


def _tokenize_generic(code: str) -> list[TokenItem]:
    without_hash_comments = re.sub(r"#.*", "", code)
    return _regex_tokenize_with_lines(_strip_java_comments(without_hash_comments))


def _regex_tokenize_with_lines(code: str) -> list[TokenItem]:
    tokens: list[TokenItem] = []
    line = 1
    last_index = 0
    for match in JAVA_TOKEN_PATTERN.finditer(code):
        line += code.count("\n", last_index, match.start())
        line_start = code.rfind("\n", 0, match.start()) + 1
        tokens.append(TokenItem(match.group(0), line, match.start() - line_start,
                                line + code.count("\n", match.start(), match.end())))
        line += code.count("\n", match.start(), match.end())
        last_index = match.end()
    return tokens


def _strip_java_comments(code: str) -> str:
    return mask_comments(code)[0]


def _fingerprints(tokens: list[str]) -> set[tuple[str, ...]]:
    if not tokens:
        return set()
    size = _ngram_size(len(tokens))
    if len(tokens) <= size:
        return {tuple(tokens)}
    return {tuple(tokens[index : index + size]) for index in range(0, len(tokens) - size + 1)}


def _fingerprint_locations(tokens: list[TokenItem]) -> dict[tuple[str, ...], tuple[int, int]]:
    if not tokens:
        return {}
    size = _ngram_size(len(tokens))
    if len(tokens) <= size:
        return {tuple(item.value for item in tokens): (tokens[0].line, tokens[-1].end_line or tokens[-1].line)}

    locations: dict[tuple[str, ...], tuple[int, int]] = {}
    for index in range(0, len(tokens) - size + 1):
        window = tokens[index : index + size]
        fingerprint = tuple(item.value for item in window)
        locations.setdefault(fingerprint, (window[0].line, window[-1].end_line or window[-1].line))
    return locations


def _overlap_fragments(tokens_a: list[TokenItem], tokens_b: list[TokenItem]) -> list[dict[str, object]]:
    locations_a = _fingerprint_locations(tokens_a)
    locations_b = _fingerprint_locations(tokens_b)
    overlaps = locations_a.keys() & locations_b.keys()
    fragments = []
    for fingerprint in sorted(overlaps, key=lambda item: (locations_a[item][0], locations_b[item][0], item)):
        a_start, a_end = locations_a[fingerprint]
        b_start, b_end = locations_b[fingerprint]
        fragments.append(
            {
                "tokens": list(fingerprint),
                "submissionAStartLine": a_start,
                "submissionAEndLine": a_end,
                "submissionBStartLine": b_start,
                "submissionBEndLine": b_end,
            }
        )
        if len(fragments) >= MAX_EVIDENCE_FRAGMENTS:
            break
    return fragments


def _overlap_ast_fragments(nodes_a: list[AstNodeItem], nodes_b: list[AstNodeItem]) -> list[dict[str, object]]:
    locations_a = _ast_fingerprint_locations(nodes_a)
    locations_b = _ast_fingerprint_locations(nodes_b)
    overlaps = locations_a.keys() & locations_b.keys()
    fragments = []
    for fingerprint in sorted(overlaps, key=lambda item: (locations_a[item][0], locations_b[item][0], item)):
        a_start, a_end = locations_a[fingerprint]
        b_start, b_end = locations_b[fingerprint]
        fragments.append(
            {
                "nodes": list(fingerprint),
                "submissionAStartLine": a_start,
                "submissionAEndLine": a_end,
                "submissionBStartLine": b_start,
                "submissionBEndLine": b_end,
            }
        )
        if len(fragments) >= MAX_EVIDENCE_FRAGMENTS:
            break
    return fragments


def _ast_fingerprint_locations(nodes: list[AstNodeItem]) -> dict[tuple[str, ...], tuple[int, int]]:
    if not nodes:
        return {}
    size = _ngram_size(len(nodes))
    if len(nodes) <= size:
        return {tuple(item.value for item in nodes): (min(n.line for n in nodes), max(n.line for n in nodes))}
    locations: dict[tuple[str, ...], tuple[int, int]] = {}
    for index in range(0, len(nodes) - size + 1):
        window = nodes[index : index + size]
        fingerprint = tuple(item.value for item in window)
        locations.setdefault(fingerprint, (min(n.line for n in window), max(n.line for n in window)))
    return locations


def _sequence_similarity(left: list[str], right: list[str]) -> float:
    return _jaccard(_fingerprints(left), _fingerprints(right))


def _ngram_size(token_count: int) -> int:
    if token_count < 3:
        return 1
    if token_count < 8:
        return 2
    return 3


def _jaccard(left: set[tuple[str, ...]], right: set[tuple[str, ...]]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _weighted_similarity(
    token_similarity: float,
    ast_similarity: float,
    canonical_similarity: float,
    identifier_mapping_similarity: float,
    ast_enabled: bool,
    canonical_enabled: bool,
) -> float:
    if ast_enabled and canonical_enabled:
        return (
            (0.20 * token_similarity)
            + (0.20 * ast_similarity)
            + (0.45 * canonical_similarity)
            + (0.15 * identifier_mapping_similarity)
        )
    return token_similarity


def _identifier_kind(tokens: list[str], index: int, language: str) -> str | None:
    value = tokens[index]
    if not _is_identifier(value, language):
        return None
    previous = tokens[index - 1] if index > 0 else ""
    next_value = tokens[index + 1] if index + 1 < len(tokens) else ""
    if previous == "class":
        return "CLASS"
    if previous == "def" or _looks_like_function_name(tokens, index, language, next_value):
        return "FUNC"
    return "VAR"


def _looks_like_function_name(tokens: list[str], index: int, language: str, next_value: str) -> bool:
    if next_value != "(":
        return False
    previous = tokens[index - 1] if index > 0 else ""
    if previous in {"if", "for", "while", "switch", "catch", "new", "return", "class", "def", "."}:
        return False
    if language.lower() in {"python", "py"} and previous in {"elif", "with", "except"}:
        return False
    return True


def _is_identifier(value: str, language: str) -> bool:
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value):
        return False
    normalized_language = language.lower()
    if normalized_language in {"python", "py"}:
        return not keyword.iskeyword(value)
    if normalized_language == "java":
        return value not in JAVA_KEYWORDS
    return value not in JAVA_KEYWORDS and not keyword.iskeyword(value)


def _reason_summary(risk_level: str, exceed_threshold: bool, cross_language_experimental: bool = False) -> str:
    if cross_language_experimental:
        return '跨语言 IR 与轻量控制/数据流摘要均为实验性零权重指标，仅供人工复核参考；不构建完整 CFG/DFG，不代表语义等价，综合风险仍使用既有生产公式。'
    if risk_level == "HIGH":
        return "相似度明显超过题目动态阈值，建议结合结构化证据进行人工复核。"
    if exceed_threshold:
        return "相似度已超过题目动态阈值，建议查看规范化与结构证据。"
    if risk_level == "MEDIUM":
        return "存在一定相似信号，但尚未超过题目动态阈值，建议按需复核。"
    return "当前相似证据低于题目动态阈值，仍可结合具体教学场景抽查。"


JAVA_KEYWORDS = {
    "abstract",
    "assert",
    "boolean",
    "break",
    "byte",
    "case",
    "catch",
    "char",
    "class",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extends",
    "final",
    "finally",
    "float",
    "for",
    "goto",
    "if",
    "implements",
    "import",
    "instanceof",
    "int",
    "interface",
    "long",
    "native",
    "new",
    "package",
    "private",
    "protected",
    "public",
    "return",
    "short",
    "static",
    "strictfp",
    "super",
    "switch",
    "synchronized",
    "this",
    "throw",
    "throws",
    "transient",
    "try",
    "void",
    "volatile",
    "while",
    "true",
    "false",
    "null",
}
