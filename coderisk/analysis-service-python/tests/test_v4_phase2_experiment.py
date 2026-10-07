import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / 'experiment'
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from run_v4_phase2_crosslang import run  # noqa: E402


def test_phase2_experiment_is_reproducible_and_keeps_production_isolated(tmp_path: Path) -> None:
    dataset = ROOT / 'experiment/datasets/v4-phase2-crosslang/cases.json'
    output = tmp_path / 'phase2-run'

    result = run(dataset, output, 'TEST-V4-PHASE2')

    manifest = result['manifest']
    assert manifest['caseCount'] == 7
    assert manifest['productionScoreIntegration'] is False
    assert manifest['testSetModifiedDuringRun'] is False
    assert manifest['formulaVersion'] == 'FORMULA_SPEC_V1'
    assert (output / 'run_manifest.json').is_file()
    assert (output / 'metric_comparison.csv').is_file()
    assert (output / 'failure_cases.csv').is_file()
    assert (output / 'experiment_report.md').is_file()

    payload = json.loads((output / 'results.json').read_text(encoding='utf-8'))
    assert len(payload['cases']) == 7
    parse_failure = next(item for item in payload['cases'] if item['caseType'] == 'PARSER_FAILURE')
    assert parse_failure['parseFallback'] is True
    assert parse_failure['irSimilarity'] == 0.0
    assert parse_failure['controlSummarySimilarity'] == 0.0
    assert parse_failure['dataFlowSummarySimilarity'] == 0.0

    with (output / 'metric_comparison.csv').open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 7
    assert {'tokenSimilarity', 'astSimilarity', 'canonicalTokenSimilarity', 'irSimilarity',
            'controlSummarySimilarity', 'dataFlowSummarySimilarity'} <= set(rows[0])
