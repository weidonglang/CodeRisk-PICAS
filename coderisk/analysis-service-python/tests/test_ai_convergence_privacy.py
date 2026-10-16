from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiment"))
from ai_convergence.examples.make_seed import make_seed
from ai_convergence.build_pairs import build
from ai_convergence.validate import validate
from ai_convergence import prepare_review as review_module
from ai_convergence import protocol as protocol_module


def test_real_review_snapshot_cannot_be_written_to_public_or_arbitrary_directory(tmp_path, monkeypatch):
    source = make_seed(tmp_path / "source")
    build(source, tmp_path / "dataset")
    corpus, texts, report = validate(source)
    # UNIT_TEST_ONLY: simulate the privacy flag, not authentic real author records.
    private = corpus.model_copy(update={"artifacts": [s.model_copy(update={"synthetic": False}) for s in corpus.artifacts]})
    monkeypatch.setattr(review_module, "validate", lambda _: (private, texts, report))
    # Isolate the policy root: pytest's own temp directory may be inside project/output.
    monkeypatch.setattr(protocol_module, "__file__", str(
        tmp_path / "isolated-project/coderisk/experiment/ai_convergence/protocol.py"))
    with pytest.raises(ValueError, match="ignored"):
        review_module.prepare(source, tmp_path / "dataset/dataset.json", tmp_path / "would-leak")
    assert not (tmp_path / "would-leak").exists()


def test_private_output_policy_resolves_allowed_root_and_rejects_escape(tmp_path, monkeypatch):
    project = tmp_path / "isolated-project"
    monkeypatch.setattr(protocol_module, "__file__", str(
        project / "coderisk/experiment/ai_convergence/protocol.py"))
    protocol_module.require_private_output(True, project / "output/private-new-run")
    protocol_module.require_private_output(False, project / "public-synthetic")
    for output in (project / "evidence", project / "output/../escaped", tmp_path / "arbitrary"):
        with pytest.raises(ValueError, match="ignored"):
            protocol_module.require_private_output(True, output)
        assert not output.exists()
