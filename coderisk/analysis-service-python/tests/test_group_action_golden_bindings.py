import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from group_action_oracle import GOLD, render, validate_gold
from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.token_similarity import tokenize_code_with_locations


@pytest.mark.parametrize('gold', GOLD, ids=lambda g: g.id)
def test_exact_handwritten_binding_locations(gold):
    validate_gold(gold)
    code, occurrences = render(gold)
    result = canonicalize_code(code, gold.language, tokenize_code_with_locations(code, gold.language))
    assert result.reason is None
    expected = {(r['line'], r['column']): (r['name'], r['canonical']) for r in occurrences}
    actual = {(r['line'], r['column']): (r['rawName'], r['scopedCanonicalName']) for r in result.identifiers}
    assert actual == expected


def test_oracle_does_not_import_production_binder():
    import group_action_oracle
    source = Path(group_action_oracle.__file__).read_text(encoding='utf-8')
    assert 'from app.' not in source and 'import app.' not in source
