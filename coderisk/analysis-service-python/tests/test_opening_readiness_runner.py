import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from check_formal_readiness import ROOT, run


def test_existing_seed_cannot_be_promoted_by_preflight(tmp_path):
    output = tmp_path / 'preflight'
    report = run(ROOT / 'configs/experiments/similarity_ablation_v1.json', output,
                 ROOT / 'configs/experiments/natural_calibration_v1.json')
    assert report['status'] == 'FORMAL_BLOCKED'
    assert report['caseCount'] == 91 and report['formalEligiblePairs'] == 0
    assert report['statisticalReadiness']['status'] == 'BLOCKED_INSUFFICIENT_INDEPENDENT_REFERENCES'
    assert report['statisticalReadiness']['trustedReferencePairs'] == 0
    assert json.loads((output / 'report.json').read_text())['rows']
    with pytest.raises(FileExistsError):
        run(ROOT / 'configs/experiments/similarity_ablation_v1.json', output)
