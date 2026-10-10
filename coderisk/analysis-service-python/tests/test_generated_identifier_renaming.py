import itertools
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiment"))
from identifier_renaming import CASES, analysis, permutations, rename, run


@pytest.mark.parametrize("language,code", [
    ("python", "def fold(value):\n    result=value+1\n    return result\nfold(value=2)\n"),
    ("java", "class Main { int fold(int value) { int result=value+1; return result; } }"),
])
@pytest.mark.parametrize("names", list(itertools.permutations(["fold", "value", "result"])))
def test_all_six_fixed_domain_permutations_preserve_representation(language, code, names):
    domain = ["fold", "value", "result"]
    changed = rename(code, language, domain, dict(zip(domain, names)))
    assert analysis(changed, language).tokens == analysis(code, language).tokens


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_generated_group_action_and_inverse_are_not_just_similarity_scores(case):
    code, language, domain = case["code"], case["language"], case["domain"]
    maps = permutations(domain, 12, 20261010)
    for first, second in zip(maps, maps[1:]):
        changed = rename(code, language, domain, first)
        assert analysis(changed, language).tokens == analysis(code, language).tokens
        assert rename(changed, language, domain, {value: key for key, value in first.items()}) == code
        composition = {name: second[first[name]] for name in domain}
        assert rename(changed, language, domain, second) == rename(code, language, domain, composition)


@pytest.mark.parametrize("domain,mapping", [
    (["value", "result"], {"value": "result", "result": "result"}),
    (["value", "result"], {"value": "result"}),
    (["value", "print"], {"value": "print", "print": "value"}),
    (["value", "class"], {"value": "class", "class": "value"}),
])
def test_illegal_collision_capture_or_reserved_name_requests_are_rejected(domain, mapping):
    with pytest.raises(ValueError, match="RENAME_"):
        rename("value=1\nresult=value\n", "python", domain, mapping)


@pytest.mark.parametrize("code,domain", [
    ("value=external\n", ["value", "external"]),
    ("value=obj.value\n", ["value", "other"]),
    ("import math\nvalue=math.pi\n", ["value", "math"]),
    ("value=1\nprint(globals()['value'])\n", ["value", "other"]),
])
def test_external_or_dynamic_names_cannot_be_silently_renamed(code, domain):
    with pytest.raises(ValueError, match="RENAME_"):
        rename(code, "python", domain, dict(zip(domain, reversed(domain))))


def test_java_unmodeled_loop_subset_rejected_by_probe_generator():
    with pytest.raises(ValueError, match="RENAME_JAVA_SUBSET_UNSUPPORTED"):
        rename("class Main { void f(){for(int value=0;value<2;value++) {}} }", "java", ["value", "other"], {"value": "other", "other": "value"})


def test_probe_outputs_are_deterministic_synthetic_and_immutable(tmp_path):
    first, second = tmp_path / "one", tmp_path / "two"
    result = run(first, count=4, seed=5)
    assert result["passed"] == 24 and result["failed"] == result["formalEligiblePairs"] == 0
    assert result["productionFormulaChanged"] is False
    run(second, count=4, seed=5)
    assert (first / "variants.jsonl").read_bytes() == (second / "variants.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        run(first, count=4, seed=5)
