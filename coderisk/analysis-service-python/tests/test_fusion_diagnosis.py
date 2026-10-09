"""Algebra and frozen decision checks on artificial fixtures."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiment'))
from diagnose_fusion import confusion, decompose


def test_decomposition_reconstructs_score_and_rejects_other_weights():
    row={'raw':.2,'ast':.4,'canonical':.8,'mapping':.6,'fusion_enabled':True,
         'FULL_FIXED':.57,'NO_CANONICAL_FIXED':.3}
    result=decompose(row)
    assert result['canonical_contribution']==pytest.approx(.225)
    assert result['mapping_contribution']==pytest.approx(.045)
    with pytest.raises(ValueError,match='formula mismatch'):
        decompose({**row,'FULL_FIXED':.75})


def test_fallback_cannot_be_attributed_to_canonicalization():
    r=decompose({'raw':.2,'ast':0,'canonical':0,'mapping':0,'fusion_enabled':False,
                 'FULL_FIXED':.2,'NO_CANONICAL_FIXED':.2})
    assert r['canonical_contribution']==r['mapping_contribution']==0
    assert confusion([{'published_verdict':1,'score':.5},{'published_verdict':0,'score':.5}], 'score',.5)=={
        'n':2,'tp':1,'fp':1,'tn':0,'fn':0,'f1':2/3,'fpr':1.}
