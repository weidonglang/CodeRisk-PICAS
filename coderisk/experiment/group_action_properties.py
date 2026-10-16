"""Independent-gold finite properties AND lossy-representation counterprobes.

Self-authored development mechanisms, not human labels or a benchmark. Outputs
are immutable. Only explicitly supplied javac compiles these self-authored golds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis-service-python'))
from app.analyzers.canonicalization import canonicalize_code
from app.analyzers.problem_profile import FORMULA_VERSION
from app.analyzers.token_similarity import tokenize_code_with_locations, _fingerprints
from group_action_oracle import BOUNDARIES, GOLD, MARKER, action, render, validate_gold
from identifier_renaming import permutations
from research_v4_dataset import _write_csv as write_csv
from similarity_ablation import extract_case


def digest(value):
    return hashlib.sha256(value).hexdigest()


def normalize(code, language):
    return canonicalize_code(code, language, tokenize_code_with_locations(code, language))


def binding_matches(result, occurrences):
    expected = {(r['line'], r['column']): (r['name'], r['canonical']) for r in occurrences}
    actual = {(r['line'], r['column']): (r['rawName'], r['scopedCanonicalName']) for r in result.identifiers}
    return actual == expected


def scored_probe(identifier, language, a, b):
    case = {'pair_id': identifier, 'split': 'validation', 'experiment_label': 'UNCERTAIN',
            'problem_id': identifier, 'source_id': identifier, 'source_type': 'synthetic', 'synthetic': True,
            'language_a': language, 'language_b': language, 'case_type': 'MECHANISM_NOT_RELATION_LABEL',
            'problem_type': 'correctness_probe', 'code_a': a, 'code_b': b,
            'code_a_sha256': digest(a.encode()), 'code_b_sha256': digest(b.encode()),
            'question': {'title': 'Self-authored mechanism probe', 'description': 'Not a real assignment pair or independent-source label.'}}
    row = extract_case(case, 1, identifier)
    left, right = normalize(a, language), normalize(b, language)
    return {**row, 'formal_eligible': False, 'canonical_sequence_equal': left.tokens == right.tokens,
            'canonical_fingerprint_equal': _fingerprints(left.tokens) == _fingerprints(right.tokens),
            'source_a': a, 'source_b': b}


def discrimination_probes():
    source, _ = render(next(g for g in GOLD if g.id == 'py-shared-spelling'))
    local_alpha = 'def fold(left):\n    return left + 1\ndef process(right):\n    return right + 2\n'
    prefix, step, suffix = 'def fold(value):\n    total = value\n', '    total = total + 1\n', '    return total\n'
    original = 'def fold(value):\n    return value + 1\n'
    return [scored_probe('ALPHA_NOT_UNIFORM_ORBIT', 'python', source, local_alpha),
            scored_probe('REPETITION_NGRAM_COLLISION', 'python', prefix + step * 2 + suffix, prefix + step * 3 + suffix),
            scored_probe('OPERATOR_CHANGE', 'python', original, original.replace('+', '-')),
            scored_probe('STATEMENT_INSERTION', 'python', original, 'def fold(value):\n    print(value)\n    return value + 1\n')]


def run(output, seeds=(20261011, 73, 901), variants=48, javac=None):
    if variants < 2 or variants > 720 or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('Use distinct fixed seeds and 2..720 permutations of each six-name domain')
    output.mkdir(parents=True, exist_ok=False)
    started, clock = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    config = {'protocolVersion': 'independent-gold-properties-v1', 'seeds': list(seeds),
              'variantsPerFixturePerSeed': variants, 'sourceType': 'synthetic', 'formalEligible': False}
    rows, bindings, compile_records, sensitivity = [], [], [], []
    for gold in GOLD:
        code, occurrences = render(gold)
        bindings.extend({'fixture': gold.id, 'language': gold.language, **r} for r in occurrences)
        validate_gold(gold)
        base = normalize(code, gold.language)
        base_ok = base.reason is None and binding_matches(base, occurrences)
        for seed in seeds:
            maps = permutations(list(gold.domain), variants, seed)
            for index, mapping in enumerate(maps):
                begin = time.perf_counter_ns()
                transformed = action(code, gold.language, gold.domain, mapping)
                transformed_gold = replace(gold, marked=MARKER.sub(
                    lambda m: '{{' + m[1] + ':' + mapping.get(m[2], m[2]) + '}}', gold.marked))
                independent_code, expected_occurrences = render(transformed_gold)
                result = normalize(transformed, gold.language)
                inverse = {new: old for old, new in mapping.items()}
                h = maps[-1]
                composition = {name: h[mapping[name]] for name in gold.domain}
                checks = {'gold_binding_equal': base_ok and binding_matches(result, expected_occurrences),
                          'independent_rewrite_equal': transformed == independent_code,
                          'canonical_sequence_equal': base.tokens == result.tokens,
                          'inverse_equal': action(transformed, gold.language, gold.domain, inverse) == code,
                          'composition_equal': action(transformed, gold.language, gold.domain, h) == action(code, gold.language, gold.domain, composition),
                          'identity_equal': action(code, gold.language, gold.domain, dict(zip(gold.domain, gold.domain))) == code}
                rows.append({'fixture': gold.id, 'language': gold.language, 'seed': seed, 'variant': index,
                             'status': 'ACCEPTED_VALID', 'passed': all(checks.values()), **checks,
                             'mapping': json.dumps(mapping, sort_keys=True), 'reason': result.reason,
                             'source_sha256': digest(code.encode()), 'variant_sha256': digest(transformed.encode()),
                             'canonical_sha256': digest(json.dumps(result.tokens).encode()),
                             'elapsed_ms': (time.perf_counter_ns() - begin) / 1e6})
                if index < 6:
                    scored = scored_probe(gold.id, gold.language, code, transformed)
                    sensitivity.append({'fixture': gold.id, 'seed': seed, 'variant': index,
                        'raw': scored['raw'], 'ast': scored['ast'], 'canonical': scored['canonical'],
                        'mapping': scored['mapping'], 'full': scored['full'],
                        'raw_delta_from_identical': scored['raw'] - 1,
                        'full_delta_from_identical': scored['full'] - 1,
                        'canonical_sequence_equal': scored['canonical_sequence_equal'],
                        'formal_eligible': False, 'source_type': 'synthetic'})
                if javac is not None and gold.language == 'java' and seed == seeds[0] and index < 2:
                    directory = output / 'compile' / gold.id / str(index)
                    directory.mkdir(parents=True)
                    source = directory / 'Main.java'
                    source.write_text(transformed, encoding='utf-8')
                    try:
                        process = subprocess.run([str(javac), '-encoding', 'UTF-8', '-proc:none', str(source)],
                                                 capture_output=True, text=True, timeout=30)
                        record = {'fixture': gold.id, 'variant': index, 'status': 'PASSED' if process.returncode == 0 else 'FAILED',
                                  'exit_code': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr}
                    except (OSError, subprocess.TimeoutExpired) as error:
                        record = {'fixture': gold.id, 'variant': index, 'status': 'UNAVAILABLE', 'error': str(error)}
                    compile_records.append(record)
    for identifier, language, code, status, reason in BOUNDARIES:
        result = normalize(code, language)
        passed = None if status == 'ORACLE_UNCERTAIN' else bool(result.reason and result.reason.startswith(reason + ':') and not result.identifiers)
        rows.append({'fixture': identifier, 'language': language, 'status': status, 'passed': passed,
                     'reason': reason, 'production_mode': result.mode, 'production_reason': result.reason,
                     'source_sha256': digest(code.encode())})
    try:
        action('def f(x,y): return x+y', 'python', ('x', 'y'), {'x': 'y', 'y': 'y'})
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    rows.append({'fixture': 'nonbijective-capture', 'language': 'python', 'status': 'INVALID_CAPTURE',
                 'passed': invalid_rejected, 'reason': 'Map x->y,y->y is outside Sym(N), not a legal action'})
    probes = discrimination_probes()
    fixture_summary = []
    for gold in GOLD:
        accepted = [r for r in rows if r['fixture'] == gold.id and r['status'] == 'ACCEPTED_VALID']
        _, gold_occurrences = render(gold)
        used = {r['name'] for r in gold_occurrences} & set(gold.domain)
        fixture_summary.append({'fixture': gold.id, 'language': gold.language,
            'attempted_permutations': len(accepted), 'unique_permutations': len({r['mapping'] for r in accepted}),
            'unique_variant_sources': len({r['variant_sha256'] for r in accepted}),
            'used_domain_spellings': len(used),
            'uniform_orbit_size_under_fixed_domain': math.factorial(len(gold.domain)) // math.factorial(len(gold.domain) - len(used))})
    paths = [Path(__file__), Path(__file__).with_name('group_action_oracle.py'),
             Path(__file__).with_name('identifier_renaming.py'), ROOT / 'analysis-service-python/app/analyzers/canonicalization.py',
             ROOT / 'analysis-service-python/app/analyzers/token_similarity.py', ROOT.parent / 'coderisk_docs/FORMULA_SPEC.md']
    record = {'status': 'FAILED' if any(r['passed'] is False for r in rows) or any(r['status'] != 'PASSED' for r in compile_records) else 'COMPLETED',
              'runId': output.name, 'formulaVersion': FORMULA_VERSION, 'algorithmVersion': 'RECORDED_SOURCE_HASHES',
              'datasetVersion': 'SELF_AUTHORED_HAND_MARKED_GOLD_V1', 'randomSeeds': list(seeds),
              'configSha256': digest(json.dumps(config, sort_keys=True).encode()),
              'gitCommit': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
              'sourceHashes': {p.relative_to(ROOT.parent).as_posix(): digest(p.read_bytes()) for p in paths},
              'python': platform.python_version(), 'startedAtUtc': started,
              'completedAtUtc': datetime.now(timezone.utc).isoformat(), 'elapsedSeconds': time.perf_counter() - clock,
              'claimLevel': 'FINITE_CORRECTNESS_AND_LOSSY_MECHANISM_NOT_BENCHMARK', 'formalEligiblePairs': 0,
              'attempted': len(rows), 'statusCounts': dict(Counter(r['status'] for r in rows)),
              'acceptedPassed': sum(r['status'] == 'ACCEPTED_VALID' and r['passed'] for r in rows),
              'uniqueVariantSourcesByFixture': {r['fixture']: r['unique_variant_sources'] for r in fixture_summary},
              'countsMeaning': 'Attempted permutations include identity/repeated seed outputs; unused names create nontrivial stabilizers, not distinct independent samples',
              'failedAssertions': sum(r['passed'] is False for r in rows), 'javaCompile': compile_records,
              'javaCompileMeaning': 'Syntax/type acceptance of self-authored code, not binding or semantic equivalence proof'}
    for name, value in [('config', config), ('run_manifest', record), ('properties', rows), ('discrimination', probes),
                        ('gold_bindings', bindings), ('fixture_summary', fixture_summary), ('rename_sensitivity', sensitivity)]:
        (output / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Rows have different status-specific fields; preserve their union rather than dropping rejected attempts.
    fields = sorted(set().union(*(r.keys() for r in rows)))
    write_csv(output / 'properties.csv', [{key: r.get(key) for key in fields} for r in rows])
    write_csv(output / 'discrimination.csv', probes)
    write_csv(output / 'gold_bindings.csv', bindings)
    write_csv(output / 'fixture_summary.csv', fixture_summary)
    write_csv(output / 'rename_sensitivity.csv', sensitivity)
    report = ['# Independent finite properties and discrimination mechanisms', '',
              '**SELF-AUTHORED SYNTHETIC DEVELOPMENT; NOT A BENCHMARK.**', '',
              f"Attempted: {record['attempted']}; accepted passed: {record['acceptedPassed']}; failed: {record['failedAssertions']}.",
              'Rejected, parser-failed and uncertain cases remain in the denominator and are not invariance successes.', '',
              'Permutation count is NOT the count of distinct programs or independent observations; see fixture_summary.csv for stabilizers and unique source hashes.', '',
              '| Mechanism | C sequence equal | Canonical ngram set equal | Raw | AST | Canonical | Mapping | Full |',
              '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for p in probes:
        report.append('| ' + p['pair_id'] + ' | ' + ' | '.join(str(p[k]) for k in ('canonical_sequence_equal', 'canonical_fingerprint_equal', 'raw', 'ast', 'canonical', 'mapping', 'full')) + ' |')
    report += ['', 'Uniform spelling orbits are narrower than local alpha equivalence. Ngram equality is weaker than C equality.',
               'No independent human relation labels, precision/recall claim, plagiarism verdict, or general semantic equivalence claim.', '']
    (output / 'REPORT.md').write_text('\n'.join(report), encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=[20261011, 73, 901])
    parser.add_argument('--variants', type=int, default=48)
    parser.add_argument('--javac', type=Path, help='Explicit compiler; self-authored gold only, six bounded compile checks')
    args = parser.parse_args()
    record = run(args.output.resolve(), tuple(args.seeds), args.variants, args.javac)
    print(json.dumps({k: record[k] for k in ('status', 'attempted', 'acceptedPassed', 'failedAssertions', 'statusCounts')}))
    raise SystemExit(0 if record['status'] == 'COMPLETED' else 1)


if __name__ == '__main__':
    main()
