"""Audit exact duplicates and overlap, without using detector scores or running sources."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from acquire_irplag import ROOT, verify
from acquire_public_datasets import digest, write_json


def audit(intake:Path,previous:Path,output:Path):
    verify(intake)
    sources=[json.loads(l) for l in (intake/'source_registry.jsonl').read_text(encoding='utf-8').splitlines()]
    pairs=[json.loads(l) for l in (intake/'published_pairs.jsonl').read_text(encoding='utf-8').splitlines()]
    old=[json.loads(l) for l in previous.read_text(encoding='utf-8').splitlines()]
    group=defaultdict(list)
    for r in sources:group[r['code_sha256_bytes']].append(r)
    index={r['source_id']:r for r in sources}
    dups=[{'sha256':h,'source_ids':[r['source_id'] for r in rows],
           'problems':sorted({r['problem_id'] for r in rows}),'categories':dict(Counter(r['category'] for r in rows))}
          for h,rows in group.items() if len(rows)>1]
    identical=[{'pair_id':p['pair_id'],'published_verdict':p['published_verdict'],'disputed':p['public_label_disputed']}
               for p in pairs if index[p['source_a']]['code_sha256_bytes']==index[p['source_b']]['code_sha256_bytes']]
    old_hash={r['code_sha256_bytes'] for r in old}
    unique_pairs=defaultdict(set)
    for p in pairs:
        if not p['public_label_disputed']:
            unique_pairs[p['published_verdict']].add(tuple(sorted((index[p['source_a']]['code_sha256_bytes'],index[p['source_b']]['code_sha256_bytes']))))
    value={'input_sha256':{str(previous.relative_to(ROOT)):digest(previous.read_bytes()),
                           'source_registry.jsonl':digest((intake/'source_registry.jsonl').read_bytes())},
           'logical_sources':len(sources),'unique_byte_hashes':len(group),'duplicate_byte_groups':dups,
           'identical_reference_pairs':identical,'cross_previous_intake_source_hash_matches':sum(r['code_sha256_bytes'] in old_hash for r in sources),
           'uncontested_unique_reference_pairs_by_published_label':{str(label):len(items) for label,items in sorted(unique_pairs.items())},
           'selection_uses_detector_scores':False,'code_executed':False,
           'statement':'Hash equality does not override publisher relationship labels. Deduplicate statistical units, retain provenance, and never count repeated variants as independent evidence.'}
    write_json(output,value)
    return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--intake',type=Path,default=ROOT/'data/public-datasets/irplag-20261009')
    parser.add_argument('--previous',type=Path,default=ROOT/'experiment/evidence/data-quality-20261009/source_quality_registry.jsonl')
    parser.add_argument('--output',type=Path,default=ROOT/'experiment/evidence/irplag-intake-20261009/quality_summary.json')
    args=parser.parse_args()
    print(json.dumps(audit(args.intake,args.previous,args.output),ensure_ascii=False,indent=2))
