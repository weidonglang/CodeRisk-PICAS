"""Capture-avoiding fixed-domain rename probes; self-authored, never benchmark labels."""
from __future__ import annotations

import argparse
import ast
import builtins
from datetime import datetime, timezone
import hashlib
import io
import json
import keyword
from pathlib import Path
import platform
import random
import re
import subprocess
import sys
import time
import tokenize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis-service-python"))
from app.analyzers.canonicalization import canonicalize_code, JAVA_KEYWORDS
from app.analyzers.token_similarity import tokenize_code_with_locations
from app.analyzers.problem_profile import FORMULA_VERSION

PROBE_VERSION = "canonical-research-alpha-v1"
CASES = [
    {"id": "python-keyword", "language": "python", "domain": ["fold", "value", "result", "alpha", "beta", "gamma"],
     "code": "def fold(value):\n    result = value + 1\n    return result\nfold(value=2)\n"},
    {"id": "python-shadow", "language": "python", "domain": ["outer", "inner", "value", "total", "alpha", "beta"],
     "code": "def outer(value):\n    total = value\n    def inner(value):\n        total = value + 1\n        return total\n    return inner(value=total)\nouter(value=2)\n"},
    {"id": "python-lambda-default", "language": "python", "domain": ["seed", "func", "value", "result", "alpha", "beta"],
     "code": "seed = 1\nfunc = lambda value=seed: value + seed\nresult = func(2)\n"},
    {"id": "python-library", "language": "python", "domain": ["solve", "values", "total", "alpha", "beta", "gamma"],
     "code": "def solve(values):\n    total = len(values)\n    print(total)\n    return total\nsolve((1, 2))\n"},
    {"id": "java-method", "language": "java", "domain": ["fold", "value", "result", "alpha", "beta", "gamma"],
     "code": "class Main { int fold(int value) { int result = value + 1; System.out.println(result); return result; } }"},
    {"id": "java-blocks", "language": "java", "domain": ["fold", "value", "left", "right", "alpha", "beta"],
     "code": "class Main { int fold(int value) { if (value > 0) { int left = value + 1; return left; } else { int right = value - 1; return right; } } }"},
]


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def analysis(code: str, language: str):
    return canonicalize_code(code, language, tokenize_code_with_locations(code, language))


def validate_permutation(domain, mapping: dict[str, str], language: str):
    names = set(domain)
    reserved = set(keyword.kwlist) | set(dir(builtins)) if language == "python" else JAVA_KEYWORDS | {"Main", "main", "System", "out", "println", "String"}
    if not names or len(names) != len(domain) or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or name in reserved for name in names):
        raise ValueError("RENAME_DOMAIN_INVALID: unique ASCII names, fixed keywords/builtins/API required")
    if set(mapping) != names or set(mapping.values()) != names or len(set(mapping.values())) != len(mapping):
        raise ValueError("RENAME_NOT_A_PERMUTATION: complete fixed-domain bijection required; capture/collision rejected")


def rename(code: str, language: str, domain: list[str], mapping: dict[str, str]) -> str:
    validate_permutation(domain, mapping, language)
    result = analysis(code, language)
    if result.mode == "lexical-fallback":
        raise ValueError("RENAME_UNSUPPORTED: " + (result.reason or "binding unavailable"))
    names = set(domain)
    tokens = tokenize_code_with_locations(code, language)
    if language == "python":
        tree = ast.parse(code)
        protected = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                protected.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
                protected.update(alias.name for alias in node.names)
        if protected & names:
            raise ValueError("RENAME_EXTERNAL_NAME_FIXED: import/attribute names cannot enter the domain")
        # Tokenizer is an independent rewrite mechanism: it includes keyword labels,
        # not just the production canonical occurrence list whose bugs we are testing.
        positions = {(item.start[0], item.start[1]) for item in tokenize.generate_tokens(io.StringIO(code).readline)
                     if item.type == tokenize.NAME and item.string in names}
    else:
        if any(token.value in {"for", "catch", "interface", "enum", "record", "->", "::", "throws", "new"} for token in tokens):
            raise ValueError("RENAME_JAVA_SUBSET_UNSUPPORTED: only primitive, brace-scoped test programs")
        if any(item["kind"] == "CLASS" and item["rawName"] in names for item in result.identifiers):
            raise ValueError("RENAME_EXTERNAL_NAME_FIXED: Java class/file identity fixed in this prototype")
        positions = {(item.line, item.column) for item in tokens if item.value in names}
    bound_positions = {(int(item["line"]), int(item["column"])) for item in result.identifiers}
    if not positions <= bound_positions:
        raise ValueError("RENAME_EXTERNAL_NAME_FIXED: domain occurs as an unresolved/free/external token")
    lines = code.splitlines(keepends=True)
    offsets, total = [], 0
    for line in lines:
        offsets.append(total)
        total += len(line)
    edits = [(offsets[item.line - 1] + item.column, item.value, mapping[item.value])
             for item in tokens if (item.line, item.column) in positions]
    for offset, original, replacement in sorted(edits, reverse=True):
        if code[offset:offset + len(original)] != original:
            raise ValueError("RENAME_LOCATION_INVALID")
        code = code[:offset] + replacement + code[offset + len(original):]
    if language == "python":
        # Compile validates binding-related syntax too (e.g. duplicate parameters); it does not execute.
        compile(code, "<synthetic-rename-probe>", "exec")
    # A permutation of all bound spellings fixes external names and preserves equality/shadowing.
    return code


def permutations(domain: list[str], count: int, seed: int):
    if count < 1:
        raise ValueError("At least one variant required")
    import math
    if count > math.factorial(len(domain)):
        raise ValueError("Requested more distinct permutations than the fixed domain permits")
    rng = random.Random(seed)
    values = [tuple(domain)]
    seen = set(values)
    while len(values) < count:
        candidate = list(domain)
        rng.shuffle(candidate)
        key = tuple(candidate)
        if key not in seen:
            values.append(key)
            seen.add(key)
    return [dict(zip(domain, value)) for value in values]


def run(output: Path, count: int = 48, seed: int = 20261010, java_compiler: Path | None = None):
    if output.exists():
        raise FileExistsError("Probe output is immutable; choose a new directory")
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    records = []
    for case in CASES:
        code, language, domain = case["code"], case["language"], case["domain"]
        base = analysis(code, language)
        maps = permutations(domain, count, seed)
        for index, mapping in enumerate(maps):
            variant = rename(code, language, domain, mapping)
            normalized = analysis(variant, language)
            inverse = {value: key for key, value in mapping.items()}
            inverse_ok = rename(variant, language, domain, inverse) == code
            second = maps[(index + 1) % len(maps)]
            composed = {name: second[mapping[name]] for name in domain}
            composition_ok = rename(variant, language, domain, second) == rename(code, language, domain, composed)
            records.append({"case_id": case["id"], "language": language, "variant_index": index,
                            "source_type": "synthetic", "purpose": "correctness_probe_not_benchmark",
                            "eligible_for_core_metrics": False, "mapping": mapping, "code": variant,
                            "base_code_sha256": sha(code), "variant_code_sha256": sha(variant),
                            "canonical_sha256": sha(json.dumps(normalized.tokens, ensure_ascii=True)),
                            "canonical_equal": normalized.tokens == base.tokens and normalized.mode != "lexical-fallback",
                            "inverse_action_equal": inverse_ok, "composition_action_equal": composition_ok})
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    except (OSError, subprocess.SubprocessError):
        git_commit = "UNAVAILABLE"
    files = [Path(__file__), ROOT / "analysis-service-python/app/analyzers/canonicalization.py",
             ROOT / "analysis-service-python/app/analyzers/token_similarity.py", ROOT.parent / "coderisk_docs/FORMULA_SPEC.md"]
    passed = sum(row["canonical_equal"] and row["inverse_action_equal"] and row["composition_action_equal"] for row in records)
    summary = {"probeVersion": PROBE_VERSION, "algorithmVersion": "source-hashes-recorded-not-a-benchmark",
               "formulaVersion": FORMULA_VERSION, "datasetVersion": "self-authored-alpha-fixtures-v1",
               "randomSeed": seed, "runId": output.name, "gitCommit": git_commit, "startedAtUtc": started,
               "normalizationElapsedSeconds": round(time.perf_counter() - clock, 6), "pythonVersion": platform.python_version(),
               "sourceHashes": {str(path.relative_to(ROOT.parent)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
               "fixtureCount": len(CASES), "generatedVariants": len(records), "passed": passed,
               "failed": len(records) - passed, "groupLawChecks": 2 * len(records), "formalEligiblePairs": 0,
               "productionFormulaChanged": False, "proofStatus": "conditional-proof-sketch-plus-finite-tests-not-machine-proof"}
    output.mkdir(parents=True)
    compilation = {"status": "NOT_RUN", "scope": "first_six_variants_per_java_fixture", "passed": 0, "failed": 0}
    if java_compiler is not None:
        compilation["status"] = "RUN"
        compilation["compiler"] = str(java_compiler.resolve())
        compilation["compilerVersion"] = subprocess.check_output([str(java_compiler), "-version"], stderr=subprocess.STDOUT).decode().strip()
        for record in records:
            if record["language"] != "java" or record["variant_index"] >= 6:
                continue
            folder = output / "java_compile" / f"{record['case_id']}-{record['variant_index']}"
            folder.mkdir(parents=True)
            source = folder / "Main.java"
            source.write_text(record["code"], encoding="utf-8")
            process = subprocess.run([str(java_compiler), "-encoding", "UTF-8", "-d", str(folder), str(source)], capture_output=True, timeout=30)
            compilation["passed" if process.returncode == 0 else "failed"] += 1
            (folder / "compiler.txt").write_text(process.stdout.decode(errors="replace") + process.stderr.decode(errors="replace"), encoding="utf-8")
        summary["failed"] += compilation["failed"]
    summary["javaCompilation"] = compilation
    summary["elapsedSeconds"] = round(time.perf_counter() - clock, 6)
    for name, value in (("summary.json", summary), ("fixtures.json", CASES)):
        with (output / name).open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
    with (output / "variants.jsonl").open("x", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    with (output / "REPORT.md").open("x", encoding="utf-8") as handle:
        handle.write(f"# Identifier rename correctness probes\n\n{passed}/{len(records)} variants pass canonical equality, inverse and composition checks.\n\n"
                     "Self-authored synthetic correctness fixtures only. No public benchmark scores, semantic equivalence or plagiarism findings.\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variants-per-case", type=int, default=48)
    parser.add_argument("--seed", type=int, default=20261010)
    parser.add_argument("--java-compiler", type=Path, help="Optional javac; compile first six self-authored Java variants per fixture, never execute")
    args = parser.parse_args()
    result = run(args.output.resolve(), args.variants_per_case, args.seed, args.java_compiler)
    print(json.dumps(result, indent=2))
    return int(result["failed"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
