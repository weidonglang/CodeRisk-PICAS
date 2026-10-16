import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from group_action_oracle import GOLD, names, render
from test_group_action_orbits import canonical
from app.analyzers.token_similarity import _fingerprints


def test_alpha_equivalence_is_broader_than_uniform_spelling_orbit():
    source, _ = render(next(g for g in GOLD if g.id == 'py-shared-spelling'))
    other = 'def fold(left):\n    return left + 1\ndef process(right):\n    return right + 2\n'
    assert canonical(source, 'python') == canonical(other, 'python')
    # A uniform function cannot map the same source spelling to two target names.
    targets = {b[0] for a, b in zip(names(source, 'python'), names(other, 'python')) if a[0] == 'value'}
    assert targets == {'left', 'right'}


def test_ngram_set_loses_multiplicity_without_canonical_sequence_equality():
    prefix = 'def fold(value):\n    total = value\n'
    statement = '    total = total + 1\n'
    suffix = '    return total\n'
    a = canonical(prefix + statement * 2 + suffix, 'python')
    b = canonical(prefix + statement * 3 + suffix, 'python')
    assert a != b
    assert _fingerprints(a) == _fingerprints(b)


def test_operator_change_is_not_an_identifier_group_action():
    a = 'def fold(value):\n    return value + 1\n'
    b = 'def fold(value):\n    return value - 1\n'
    assert canonical(a, 'python') != canonical(b, 'python')
