import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from group_action_properties import run


def test_runner_records_all_denominators_and_refuses_overwrite(tmp_path):
    output = tmp_path / 'run'
    record = run(output, seeds=(73,), variants=2)
    assert record['status'] == 'COMPLETED'
    assert record['attempted'] == 34 and record['acceptedPassed'] == 24
    assert record['statusCounts'] == {'ACCEPTED_VALID': 24, 'REJECTED_UNSUPPORTED': 5,
                                     'PARSER_FAILURE': 2, 'ORACLE_UNCERTAIN': 2, 'INVALID_CAPTURE': 1}
    assert record['formalEligiblePairs'] == 0 and record['javaCompile'] == []
    assert record['sourceHashes'] and record['configSha256']
    probes = json.loads((output / 'discrimination.json').read_text())
    repeated = next(p for p in probes if p['pair_id'] == 'REPETITION_NGRAM_COLLISION')
    assert repeated['canonical_sequence_equal'] is False
    assert repeated['canonical'] == 1
    with pytest.raises(FileExistsError):
        run(output, seeds=(73,), variants=2)


@pytest.mark.parametrize('seeds,variants', [((73,73),2), ((),2), ((73,),0), ((73,),721)])
def test_runner_rejects_invalid_plan(tmp_path, seeds, variants):
    with pytest.raises(ValueError):
        run(tmp_path / 'invalid', seeds, variants)
