"""Decompose existing observed ConPlag pilot scores; no fitting, rescoring or new test claim."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from statistics import mean, median

from acquire_public_datasets import digest, write_json, write_rows

ROOT = Path(__file__).resolve().parents[1]


def decompose(row: dict) -> dict:
    baseline = row['NO_CANONICAL_FIXED']
    canonical = .45 * (row['canonical'] - .5 * (row['raw'] + row['ast'])) if row['fusion_enabled'] else 0.
    mapping = .15 * (row['mapping'] - .5 * (row['raw'] + row['ast'])) if row['fusion_enabled'] else 0.
    change = row['FULL_FIXED'] - baseline
    if abs(change - canonical - mapping) > 2e-6:
        raise ValueError('Frozen fusion formula mismatch; do not reinterpret scores using different weights')
    return {**row,'canonical_contribution':canonical,'mapping_contribution':mapping,'fusion_change':change}


def confusion(rows,method,threshold):
    counts=Counter(('tp' if r['published_verdict']==1 else 'fp') if r[method]>=threshold
                   else ('fn' if r['published_verdict']==1 else 'tn') for r in rows)
    tp,fp,tn,fn=(counts[k] for k in ('tp','fp','tn','fn'))
    return {'n':len(rows),'tp':tp,'fp':fp,'tn':tn,'fn':fn,
            'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
            'fpr':fp/(fp+tn) if fp+tn else None}


def run(pilot:Path,output:Path):
    records, summaries, decisions, hashes = [],[],[],{}
    for view in ('version_1','version_2'):
        file=pilot/view/'picas_scores.jsonl'
        evaluation=pilot/view/'evaluation.json'
        hashes[str(file.relative_to(ROOT))]=digest(file.read_bytes())
        hashes[str(evaluation.relative_to(ROOT))]=digest(evaluation.read_bytes())
        rows=[decompose(json.loads(line)) for line in file.read_text(encoding='utf-8').splitlines()]
        params=json.loads(evaluation.read_text())['all_picas_pairs']['parameters']
        for r in rows:
            r.update({'full_prediction':r['FULL_FIXED']>=params['FULL_FIXED'],
                      'no_canonical_prediction':r['NO_CANONICAL_FIXED']>=params['NO_CANONICAL_FIXED'],
                      'full_threshold_frozen':params['FULL_FIXED'],'no_canonical_threshold_frozen':params['NO_CANONICAL_FIXED']})
        records.extend(rows)
        for split in ('validation','test'):
            subset=[r for r in rows if r['split']==split]
            for label in (0,1):
                group=[r for r in subset if r['published_verdict']==label]
                summaries.append({'view':view,'split':split,'published_label':label,'n':len(group),
                    'fusion_enabled':sum(r['fusion_enabled'] for r in group),
                    **{f'mean_{k}':mean(r[k] for r in group) for k in ('raw','ast','canonical','mapping','canonical_contribution','mapping_contribution','fusion_change')},
                    'median_fusion_change':median(r['fusion_change'] for r in group),
                    'raised_by_fusion':sum(r['fusion_change']>2e-6 for r in group),
                    'lowered_by_fusion':sum(r['fusion_change']< -2e-6 for r in group),
                    'full_only_predicted_positive':sum(r['full_prediction'] and not r['no_canonical_prediction'] for r in group),
                    'no_canonical_only_predicted_positive':sum(not r['full_prediction'] and r['no_canonical_prediction'] for r in group)})
            for method in ('FULL_FIXED','NO_CANONICAL_FIXED'):
                decisions.append({'view':view,'split':split,'method':method,'threshold':params[method],**confusion(subset,method,params[method])})
    write_rows(output/'pair_decomposition.jsonl',records)
    for name,rows in (('component_summary.csv',summaries),('frozen_decision_summary.csv',decisions)):
        with (output/name).open('x',encoding='utf-8',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    changed=[r for r in records if r['split']=='test' and r['full_prediction']!=r['no_canonical_prediction']]
    cases=sorted(changed,key=lambda r:(r['view'],r['published_verdict'],-abs(r['fusion_change']),r['pair_id']))
    write_rows(output/'changed_decision_cases.jsonl',cases)
    plot(summaries,output/'component_contributions.png')
    manifest={'status':'EXPLORATORY_DIAGNOSIS_OF_ALREADY_OBSERVED_PILOT','input_sha256':hashes,
        'pairs_per_view':911,'thresholds_reused_from_frozen_validation_selection':True,'new_detector_runs':0,
        'new_parameter_fitting':False,'eligible_for_core_metrics':False,
        'decomposition':'full - noCanonical = .45*(canonical - .5*(raw+ast)) + .15*(mapping - .5*(raw+ast))',
        'limitations':['Different methods retain different frozen thresholds; decision changes are not isolated causal effects.',
                       'Observed test reused for diagnosis only, not a fresh held-out performance claim.',
                       'Public pair labels are from the publisher, not local double-human review.'],
        'output_sha256':{p.name:digest(p.read_bytes()) for p in output.iterdir() if p.is_file()},
        'summary':summaries,'decisions':decisions}
    write_json(output/'manifest.json',manifest)
    return decisions


def plot(summary,target):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    rows=[r for r in summary if r['split']=='test']
    x=np.arange(len(rows))
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
    labels=[f"{r['view']}\n{'published negative' if r['published_label']==0 else 'published positive'}" for r in rows]
    axes[0].bar(x-.18,[r['mean_canonical_contribution'] for r in rows],width=.36,label='Canonical contribution')
    axes[0].bar(x+.18,[r['mean_mapping_contribution'] for r in rows],width=.36,label='Identifier mapping contribution')
    axes[0].axhline(0,color='black',linewidth=.7);axes[0].set_ylabel('Mean score change vs no-canonical fusion')
    axes[0].set_xticks(x,labels,fontsize=8);axes[0].legend(fontsize=8)
    for key,color,label in [('raised_by_fusion','#bf4e30','Raised score'),('lowered_by_fusion','#357879','Lowered score')]:
        offset= -.18 if key=='raised_by_fusion' else .18
        axes[1].bar(x+offset,[r[key] for r in rows],width=.36,color=color,label=label)
    axes[1].set_xticks(x,labels,fontsize=8);axes[1].set_ylabel('Pair count');axes[1].legend(fontsize=8)
    fig.suptitle('ConPlag observed test diagnosis: descriptive, no new tuning or causal claim')
    fig.savefig(target,dpi=160);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot',type=Path,default=ROOT/'experiment/evidence/conplag-pilot-20261009')
    parser.add_argument('--output',type=Path,default=ROOT/'experiment/evidence/fusion-diagnosis-20261009')
    args=parser.parse_args()
    if args.output.exists():parser.error('Use a fresh output directory')
    args.output.mkdir(parents=True)
    print(json.dumps(run(args.pilot,args.output),indent=2))
