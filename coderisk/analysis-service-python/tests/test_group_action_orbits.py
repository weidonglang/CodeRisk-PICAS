import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from group_action_oracle import GOLD, action, render, validate_gold
from identifier_renaming import permutations
from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.token_similarity import tokenize_code_with_locations


def canonical(code, language):
    result = canonicalize_code(code, language, tokenize_code_with_locations(code, language))
    assert result.reason is None
    return result.tokens


@pytest.mark.parametrize('gold', GOLD, ids=lambda g: g.id)
@pytest.mark.parametrize('seed', [20261011, 73, 901])
def test_independent_action_identity_inverse_composition_and_invariance(gold, seed):
    validate_gold(gold)
    code, _ = render(gold)
    maps = permutations(list(gold.domain), 24, seed)
    reference = canonical(code, gold.language)
    assert action(code, gold.language, gold.domain, dict(zip(gold.domain, gold.domain))) == code
    h = maps[-1]
    for g in maps:
        changed = action(code, gold.language, gold.domain, g)
        inverse = {new: old for old, new in g.items()}
        assert action(changed, gold.language, gold.domain, inverse) == code
        composed = {name: h[g[name]] for name in gold.domain}
        assert action(changed, gold.language, gold.domain, h) == action(code, gold.language, gold.domain, composed)
        assert canonical(changed, gold.language) == reference


def test_nonbijective_capture_is_not_admitted():
    with pytest.raises(ValueError, match='INVALID_CAPTURE'):
        action('def f(x,y): return x+y', 'python', ('x', 'y'), {'x': 'y', 'y': 'y'})


def test_strings_and_external_symbols_are_fixed():
    code = 'def fold(value):\n    print("value", value)\n    return value\n'
    changed = action(code, 'python', ('fold', 'value'), {'fold': 'value', 'value': 'fold'})
    assert 'print("value", fold)' in changed
    assert canonical(code, 'python') == canonical(changed, 'python')


def test_unused_name_permutation_is_a_nonidentity_stabilizer():
    gold = next(g for g in GOLD if g.id == 'py-default-scope')
    source, _ = render(gold)
    mapping = dict(zip(gold.domain, gold.domain))
    mapping['spareone'], mapping['sparetwo'] = 'sparetwo', 'spareone'
    assert mapping != dict(zip(gold.domain, gold.domain))
    assert action(source, 'python', gold.domain, mapping) == source
