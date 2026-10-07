import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADAPTER_ROOT = ROOT / "experiment" / "baselines" / "jplag"
if str(ADAPTER_ROOT) not in sys.path:
    sys.path.insert(0, str(ADAPTER_ROOT))

from adapter import convert, convert_native_csv  # noqa: E402


def test_jplag_neutral_adapter_writes_standard_contract(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    target = tmp_path / "output.csv"
    source.write_text(
        json.dumps(
            {
                "tool": "JPLAG",
                "toolVersion": "test-version",
                "comparisons": [{"caseId": "CASE-1", "similarity": 0.875}],
            }
        ),
        encoding="utf-8",
    )

    assert convert(source, target) == 1
    with target.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {
            "caseId": "CASE-1",
            "method": "JPLAG",
            "methodVersion": "test-version",
            "predictedScore": "0.875",
        }
    ]


def test_jplag_native_csv_adapter_writes_standard_contract(tmp_path: Path) -> None:
    source = tmp_path / "results.csv"
    target = tmp_path / "standard.csv"
    source.write_text(
        "submissionName1,submissionName2,averageSimilarity,maxSimilarity\n"
        "submission-a,submission-b,1.0,1.0\n",
        encoding="utf-8",
    )

    assert convert_native_csv(source, target, "6.2.0") == 1
    with target.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [{
        "caseId": "submission-a__submission-b",
        "method": "JPLAG",
        "methodVersion": "6.2.0",
        "predictedScore": "1.0",
    }]
