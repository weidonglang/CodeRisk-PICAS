"""Metamorphic developer contracts, not measured clone-detection accuracy."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment"))
from diagnose_development_probes import DEFAULT_PROBES, compare_probe, digest, run


def test_rename_and_fallback_contracts_use_production_analyzer():
    data = json.loads(DEFAULT_PROBES.read_text(encoding="utf-8"))
    for probe in data["probes"]:
        row = compare_probe(probe, data["bases"])
        assert row["contract_passed"] is not False, probe["pair_id"]
        assert row["eligible_for_core_metrics"] is False
        assert abs(row["fusion_change"] - row["canonical_contribution"] - row["mapping_contribution"]) <= 2e-6
        assert not any(metric["name"].startswith("CROSSLANG") for metric in row["production_result"]["metrics"])


def test_diagnostics_record_sources_and_preserve_existing_outputs(tmp_path):
    output = tmp_path / "development-only"
    manifest = run(DEFAULT_PROBES, output)
    assert manifest["failed_contracts"] == []
    assert manifest["production_formula_changed"] is False
    assert manifest["parameter_fitting"] is False
    for name, expected in manifest["output_sha256"].items():
        assert digest((output / name).read_bytes()) == expected
    before = (output / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        run(DEFAULT_PROBES, output)
    assert (output / "manifest.json").read_bytes() == before


def test_diagnostics_refuse_core_dataset(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"source_type": "manual", "eligible_for_core_metrics": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="excluded from core metrics"):
        run(path, tmp_path / "output")
    assert not (tmp_path / "output").exists()
