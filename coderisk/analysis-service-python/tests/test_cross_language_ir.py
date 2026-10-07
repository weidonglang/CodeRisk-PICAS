from app.analyzers.normalized_ir import IR_VERSION, compare_normalized_ir
from app.analyzers.lightweight_summaries import (
    SUMMARY_VERSION,
    build_lightweight_summaries,
    control_summary_similarity,
    data_flow_summary_similarity,
)
from app.analyzers.token_similarity import analyze_token_pair
from app.schemas.analyze_schema import AnalyzeMockRequest


JAVA_SUM_POSITIVE = '''
class Main {
    static int sumPositive(int[] values) {
        int total = 0;
        for (int value : values) {
            if (value > 0) {
                total += value;
            }
        }
        return total;
    }
}
'''

PYTHON_SUM_POSITIVE = '''
def sum_positive(values):
    total = 0
    for value in values:
        if value > 0:
            total += value
    return total
'''

JAVA_INPUT_OUTPUT = '''
import java.util.Scanner;
class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int first = scanner.nextInt();
        int second = scanner.nextInt();
        int result = first + second;
        System.out.println(result);
    }
}
'''

PYTHON_INPUT_OUTPUT = '''
first = int(input())
second = int(input())
result = first + second
print(result)
'''


def test_java_python_loop_condition_assignment_return_ir_is_high() -> None:
    comparison = compare_normalized_ir(JAVA_SUM_POSITIVE, 'java', PYTHON_SUM_POSITIVE, 'python')

    assert comparison.comparable is True
    assert comparison.similarity >= 0.75
    assert comparison.fragments
    assert {node.kind for node in comparison.left.nodes} >= {
        'ASSIGN', 'IF', 'LOOP', 'RETURN', 'ARITH_ADD',
    }


def test_java_python_input_output_arithmetic_ir_is_high() -> None:
    comparison = compare_normalized_ir(JAVA_INPUT_OUTPUT, 'java', PYTHON_INPUT_OUTPUT, 'python')

    assert comparison.comparable is True
    assert comparison.similarity >= 0.70
    expected = {'INPUT', 'OUTPUT', 'ASSIGN', 'ARITH_ADD'}
    assert {node.kind for node in comparison.left.nodes} >= expected
    assert {node.kind for node in comparison.right.nodes} >= expected


def test_lightweight_control_and_data_flow_summaries_align() -> None:
    java = build_lightweight_summaries(JAVA_SUM_POSITIVE, 'java')
    python = build_lightweight_summaries(PYTHON_SUM_POSITIVE, 'python')

    assert java.parsed and python.parsed
    assert java.control.branch_count == python.control.branch_count == 1
    assert java.control.loop_count == python.control.loop_count == 1
    assert java.control.max_nesting_depth == python.control.max_nesting_depth == 2
    assert control_summary_similarity(java.control, python.control) == 1.0
    assert data_flow_summary_similarity(java.data, python.data) == 1.0
    assert java.data.accumulator_update_flow == ('ACCUMULATE_ADD',)
    assert python.data.return_dependency == ('RETURN_IDENTIFIER',)


def test_cross_language_mode_adds_zero_weight_metric_and_experimental_evidence() -> None:
    result = analyze_token_pair(_request(JAVA_SUM_POSITIVE, PYTHON_SUM_POSITIVE, 'PICAS_CROSSLANG'))
    ir_metric = next(metric for metric in result.metrics if metric.name == 'CROSSLANG_IR_SIMILARITY')
    ir_evidence = next(item for item in result.evidence if item.evidence_type == 'CROSSLANG_IR_MATCH')

    assert ir_metric.value >= 0.75
    assert ir_metric.weight == 0.0
    assert ir_evidence.metadata['experimental'] is True
    assert ir_evidence.metadata['includedInWeightedScore'] is False
    assert ir_evidence.metadata['irVersion'] == IR_VERSION
    metric_names = {metric.name for metric in result.metrics}
    assert 'CROSSLANG_CONTROL_SUMMARY_SIMILARITY' in metric_names
    assert 'CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY' in metric_names
    assert all(metric.weight == 0.0 for metric in result.metrics if metric.name.startswith('CROSSLANG_'))
    control_evidence = next(item for item in result.evidence if item.evidence_type == 'CONTROL_STRUCTURE_MATCH')
    data_evidence = next(item for item in result.evidence if item.evidence_type == 'OPERATION_SEQUENCE_MATCH')
    assert control_evidence.metadata['summaryVersion'] == SUMMARY_VERSION
    assert data_evidence.metadata['includedInWeightedScore'] is False


def test_standard_mode_does_not_generate_ir_metric_or_evidence() -> None:
    result = analyze_token_pair(_request(JAVA_SUM_POSITIVE, PYTHON_SUM_POSITIVE, 'PICAS_STANDARD'))

    assert all(metric.name != 'CROSSLANG_IR_SIMILARITY' for metric in result.metrics)
    assert all(not metric.name.startswith('CROSSLANG_') for metric in result.metrics)
    assert all(item.evidence_type != 'CROSSLANG_IR_MATCH' for item in result.evidence)
    assert all(item.evidence_type != 'CONTROL_STRUCTURE_MATCH' for item in result.evidence)
    assert all(item.evidence_type != 'OPERATION_SEQUENCE_MATCH' for item in result.evidence)


def test_cross_language_parse_failure_does_not_fabricate_ir_evidence() -> None:
    result = analyze_token_pair(_request(JAVA_SUM_POSITIVE, 'def broken(:\n    return 1\n', 'PICAS_CROSSLANG'))
    ir_metric = next(metric for metric in result.metrics if metric.name == 'CROSSLANG_IR_SIMILARITY')

    assert ir_metric.value == 0.0
    assert ir_metric.weight == 0.0
    assert all(item.evidence_type != 'CROSSLANG_IR_MATCH' for item in result.evidence)
    assert any(item.evidence_type == 'PARSER_WARNING' for item in result.evidence)


def _request(java_code: str, python_code: str, mode: str) -> AnalyzeMockRequest:
    return AnalyzeMockRequest.model_validate({
        'taskId': 41,
        'question': {
            'id': 9,
            'title': 'Experimental cross-language case',
            'description': 'Compare a limited Java and Python algorithm structure.',
        },
        'submissionA': {'id': 91, 'language': 'java', 'code': java_code},
        'submissionB': {'id': 92, 'language': 'python', 'code': python_code},
        'config': {'mode': mode},
    })
