from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "experiment/datasets/research-v4"
OUTPUT = DATASET_ROOT / "seed_pairs.json"
SEED_VERSION = "coderisk-research-v4-seed-1.0"


PROBLEMS = [
    ("simple_io", "G1", "Seed pair arithmetic", "Compute a small arithmetic result from two integers."),
    ("array_loop", "G2", "Seed positive aggregation", "Aggregate selected values from an integer array."),
    ("sort_template", "G3", "Seed insertion ordering", "Order integer values using a simple insertion-style template."),
    ("string_processing", "G2", "Seed character counting", "Count selected characters in a string."),
    ("dfs_graph", "G3", "Seed DFS reachability", "Count vertices reachable with a stack-based graph traversal."),
    ("bfs_graph", "G3", "Seed BFS distance", "Compute a small graph distance with queue traversal."),
    ("dp_variant", "G4", "Seed transition cost", "Compute an accumulated value with a two-state recurrence."),
    ("simulation", "G4", "Seed movement simulation", "Simulate signed movements and return the final position."),
]


SCHEDULE = {
    "validation": {
        "simple_io": ["NATURAL_TEMPLATE", "PARAMETER_RENAME", "FORMAT_COMMENT_CHANGE"],
        "array_loop": ["VARIABLE_RENAME", "LOCAL_REORDER", "INDEPENDENT_SOLUTION"],
        "sort_template": ["FUNCTION_RENAME", "HUMAN_REWRITE", "COMMON_STRUCTURE"],
        "string_processing": ["SPLIT_MERGE", "UNSUPPORTED_SYNTAX", "AI_REWRITE"],
        "dfs_graph": ["CROSSLANG_REWRITE", "VARIABLE_RENAME", "NATURAL_TEMPLATE"],
        "bfs_graph": ["HUMAN_REWRITE", "FUNCTION_RENAME", "INDEPENDENT_SOLUTION"],
        "dp_variant": ["SPLIT_MERGE", "PARAMETER_RENAME", "COMMON_STRUCTURE"],
        "simulation": ["LOCAL_REORDER", "CROSSLANG_REWRITE", "AI_REWRITE"],
    },
    "test": {
        "simple_io": ["HUMAN_REWRITE", "INDEPENDENT_SOLUTION", "CROSSLANG_REWRITE"],
        "array_loop": ["NATURAL_TEMPLATE", "VARIABLE_RENAME", "UNSUPPORTED_SYNTAX"],
        "sort_template": ["FORMAT_COMMENT_CHANGE", "LOCAL_REORDER", "AI_REWRITE"],
        "string_processing": ["FUNCTION_RENAME", "PARAMETER_RENAME", "COMMON_STRUCTURE"],
        "dfs_graph": ["SPLIT_MERGE", "HUMAN_REWRITE", "NATURAL_TEMPLATE"],
        "bfs_graph": ["CROSSLANG_REWRITE", "COMMON_STRUCTURE", "UNSUPPORTED_SYNTAX"],
        "dp_variant": ["VARIABLE_RENAME", "FORMAT_COMMENT_CHANGE", "INDEPENDENT_SOLUTION"],
        "simulation": ["LOCAL_REORDER", "SPLIT_MERGE", "AI_REWRITE"],
    },
}


JAVA_CASES = {
    ("validation", "simple_io", "FORMAT_COMMENT_CHANGE"),
    ("validation", "array_loop", "VARIABLE_RENAME"),
    ("validation", "sort_template", "FUNCTION_RENAME"),
    ("validation", "bfs_graph", "INDEPENDENT_SOLUTION"),
    ("test", "string_processing", "PARAMETER_RENAME"),
    ("test", "dp_variant", "VARIABLE_RENAME"),
    ("test", "simulation", "LOCAL_REORDER"),
    ("test", "simple_io", "INDEPENDENT_SOLUTION"),
}


def build_seed() -> dict[str, object]:
    cases: list[dict[str, object]] = []
    for split in ("validation", "test"):
        for index, (problem_type, group, title, description) in enumerate(PROBLEMS, start=1):
            tag = f"{split[:3]}_{problem_type}"
            problem_id = f"SEED-{split.upper()}-{index:02d}-{problem_type.upper().replace('_', '-')}"
            source_id = f"SEED-SOURCE-{split.upper()}-{index:02d}"
            codes = _code_family(problem_type, tag, index + (0 if split == "validation" else 20))
            for case_index, case_type in enumerate(SCHEDULE[split][problem_type], start=1):
                pair_id = f"{problem_id}-{case_index:02d}-{case_type}"
                language_a, language_b, code_a, code_b = _pair_codes(
                    split, problem_type, case_type, codes
                )
                extension_a = "java" if language_a == "java" else "py"
                extension_b = "java" if language_b == "java" else "py"
                pair_dir = DATASET_ROOT / "samples/seed" / split / problem_type / pair_id.lower()
                pair_dir.mkdir(parents=True, exist_ok=True)
                path_a = pair_dir / f"a.{extension_a}"
                path_b = pair_dir / f"b.{extension_b}"
                path_a.write_text(code_a, encoding="utf-8")
                path_b.write_text(code_b, encoding="utf-8")
                is_ai_placeholder = case_type == "AI_REWRITE"
                label = _label(case_type, is_ai_placeholder)
                cases.append({
                    "pair_id": pair_id,
                    "problem_id": problem_id,
                    "problem_type": problem_type,
                    "problem_group": group,
                    "dataset_split": split,
                    "split_preregistered": True,
                    "source_id": source_id,
                    "experiment_label": label,
                    "case_type": case_type,
                    "language": language_a if language_a == language_b else f"{language_a}-{language_b}",
                    "language_a": language_a,
                    "language_b": language_b,
                    "dataset_version": SEED_VERSION,
                    "data_origin": "SYNTHETIC",
                    "source_type": "placeholder" if is_ai_placeholder else "synthetic",
                    "synthetic": True,
                    "eligible_for_core_metrics": not is_ai_placeholder,
                    "question": {
                        "title": f"{title} ({split} synthetic seed)",
                        "description": description + " This is a synthetic seed problem used only to verify the experiment pipeline.",
                        "input_format": "Synthetic fixture input.",
                        "output_format": "Synthetic fixture output.",
                        "constraints_text": f"Seed marker {index}; not a benchmark statement.",
                    },
                    "code_a_path": path_a.relative_to(DATASET_ROOT).as_posix(),
                    "code_b_path": path_b.relative_to(DATASET_ROOT).as_posix(),
                    "code_a_sha256": _sha256(code_a),
                    "code_b_sha256": _sha256(code_b),
                    "provenance": _provenance(case_type),
                    "notes": "Synthetic seed/placeholder pair for toolchain validation only; not a real submission or benchmark case.",
                })
    return {
        "dataset_id": "coderisk-research-v4-synthetic-seed",
        "dataset_version": SEED_VERSION,
        "source_type": "synthetic",
        "status": "SYNTHETIC_SEED_ONLY",
        "description": "Deterministic synthetic seed pairs for validating ingestion, calibration, baselines, and paper export.",
        "cases": cases,
    }


def _pair_codes(
    split: str, problem_type: str, case_type: str, codes: dict[str, str]
) -> tuple[str, str, str, str]:
    if case_type == "CROSSLANG_REWRITE":
        return "python", "java", codes["python_base"], codes["java_base"]
    use_java = (split, problem_type, case_type) in JAVA_CASES
    language = "java" if use_java else "python"
    prefix = "java" if use_java else "python"
    code_a = codes[f"{prefix}_base"]
    if case_type == "VARIABLE_RENAME":
        code_b = _rename(code_a, {"values": "numbers", "value": "item", "total": "answer", "index": "cursor", "result": "output"})
    elif case_type == "FUNCTION_RENAME":
        code_b = re.sub(r"\bsolve[_A-Za-z0-9]*", "process_seed", code_a)
    elif case_type == "PARAMETER_RENAME":
        code_b = _rename(code_a, {"left": "first", "right": "second", "values": "items", "text": "content", "graph": "edges", "moves": "steps"})
    elif case_type == "FORMAT_COMMENT_CHANGE":
        code_b = ("// synthetic formatting seed\n" if use_java else "# synthetic formatting seed\n") + code_a.replace("    ", "  ")
    else:
        code_b = codes[f"{prefix}_{_variant_key(case_type)}"]
    return language, language, code_a, code_b


def _variant_key(case_type: str) -> str:
    return {
        "NATURAL_TEMPLATE": "natural",
        "INDEPENDENT_SOLUTION": "independent",
        "HUMAN_REWRITE": "human",
        "LOCAL_REORDER": "local_reorder",
        "SPLIT_MERGE": "split_merge",
        "COMMON_STRUCTURE": "common_structure",
        "UNSUPPORTED_SYNTAX": "unsupported",
        "AI_REWRITE": "ai_placeholder",
    }[case_type]


def _code_family(problem_type: str, tag: str, marker: int) -> dict[str, str]:
    python_base = _python_base(problem_type, tag, marker)
    java_base = _java_base(problem_type, tag, marker)
    return {
        "python_base": python_base,
        "python_natural": "# synthetic natural-template seed\n" + python_base.replace("return result", "return (result)"),
        "python_independent": _python_independent(problem_type, tag, marker),
        "python_human": _python_independent(problem_type, f"human_{tag}", marker) + "# scripted human-style seed rewrite\n",
        "python_local_reorder": f"seed_right_{tag} = {marker + 1}\nseed_left_{tag} = {marker}\n" + python_base,
        "python_split_merge": f"def seed_helper_{tag}(value):\n    return value\n\n" + python_base.replace("return result", f"return seed_helper_{tag}(result)"),
        "python_common_structure": f"def common_{tag}(values):\n    count = 0\n    for item in values:\n        if item:\n            count += 1\n    return count + {marker}\n",
        "python_unsupported": f"seed_generator_{tag} = (item for item in range({marker + 1}))\n" + python_base,
        "python_ai_placeholder": "# PLACEHOLDER: scripted AI-assisted slot, no model output\n" + _rename(python_base, {"result": "candidate", "total": "candidate"}),
        "java_base": java_base,
        "java_natural": "// synthetic natural-template seed\n" + java_base,
        "java_independent": _java_independent(problem_type, tag, marker),
        "java_human": "// scripted human-style seed rewrite\n" + _java_independent(problem_type, tag, marker),
        "java_local_reorder": f"// local reorder seed {marker + 1}, {marker}\n" + java_base,
        "java_split_merge": "// split/merge seed wrapper\n" + java_base,
        "java_common_structure": f"class Main {{ static int common(int[] values) {{ int count = {marker}; for (int item : values) {{ if (item != 0) count++; }} return count; }} }}\n",
        "java_unsupported": "// unsupported syntax seed\n" + java_base.replace("return result;", "java.util.function.IntUnaryOperator f = x -> x; return f.applyAsInt(result);"),
        "java_ai_placeholder": "// PLACEHOLDER: scripted AI-assisted slot, no model output\n" + java_base,
    }


def _python_base(problem_type: str, tag: str, marker: int) -> str:
    if problem_type == "simple_io":
        return f"def solve_{tag}(left, right):\n    result = left + right + {marker}\n    return result\n"
    if problem_type == "array_loop":
        return f"def solve_{tag}(values):\n    total = {marker}\n    for value in values:\n        if value > 0:\n            total += value\n    return total\n"
    if problem_type == "sort_template":
        return f"def solve_{tag}(values):\n    result = list(values)\n    for index in range(1, len(result)):\n        value = result[index]\n        cursor = index - 1\n        while cursor >= 0 and result[cursor] > value:\n            result[cursor + 1] = result[cursor]\n            cursor -= 1\n        result[cursor + 1] = value\n    return result\n"
    if problem_type == "string_processing":
        return f"def solve_{tag}(text):\n    total = {marker}\n    for value in text:\n        if value.isalpha():\n            total += 1\n    return total\n"
    if problem_type == "dfs_graph":
        return f"def solve_{tag}(graph, start):\n    seen = {{start}}\n    pending = [start]\n    while pending:\n        value = pending.pop()\n        for next_value in graph[value]:\n            if next_value not in seen:\n                seen.add(next_value)\n                pending.append(next_value)\n    result = len(seen) + {marker}\n    return result\n"
    if problem_type == "bfs_graph":
        return f"def solve_{tag}(graph, start):\n    queue = [start]\n    index = 0\n    while index < len(queue):\n        value = queue[index]\n        index += 1\n        for next_value in graph[value]:\n            if next_value not in queue:\n                queue.append(next_value)\n    result = len(queue) + {marker}\n    return result\n"
    if problem_type == "dp_variant":
        return f"def solve_{tag}(values):\n    older = {marker}\n    previous = {marker}\n    for value in values:\n        result = value + min(older, previous)\n        older = previous\n        previous = result\n    return result\n"
    return f"def solve_{tag}(moves):\n    result = {marker}\n    for value in moves:\n        if value >= 0:\n            result += value\n        else:\n            result -= -value\n    return result\n"


def _python_independent(problem_type: str, tag: str, marker: int) -> str:
    if problem_type == "simple_io":
        return f"def solve_{tag}(left, right):\n    return sum((left, right, {marker}))\n"
    if problem_type in {"array_loop", "string_processing"}:
        return f"def solve_{tag}(values):\n    selected = [item for item in values if item]\n    return len(selected) + {marker}\n"
    if problem_type == "sort_template":
        return f"def solve_{tag}(values):\n    return sorted(values)\n"
    return f"def solve_{tag}(values, start=0):\n    result = {marker}\n    for item in values:\n        result += len(item) if hasattr(item, '__len__') else int(bool(item))\n    return result + start\n"


def _java_base(problem_type: str, tag: str, marker: int) -> str:
    method = re.sub(r"[^A-Za-z0-9]", "", tag.title())
    if problem_type == "simple_io":
        body = f"static int solve{method}(int left, int right) {{ int result = left + right + {marker}; return result; }}"
    elif problem_type == "string_processing":
        body = f"static int solve{method}(String text) {{ int result = {marker}; for (int index = 0; index < text.length(); index++) {{ if (Character.isLetter(text.charAt(index))) result++; }} return result; }}"
    elif problem_type in {"dfs_graph", "bfs_graph"}:
        body = f"static int solve{method}(int[][] graph, int start) {{ int result = {marker}; for (int[] values : graph) {{ if (values.length > 0) result++; }} return result + start; }}"
    else:
        body = f"static int solve{method}(int[] values) {{ int result = {marker}; for (int value : values) {{ if (value > 0) result += value; }} return result; }}"
    return f"class Main {{ {body} }}\n"


def _java_independent(problem_type: str, tag: str, marker: int) -> str:
    method = re.sub(r"[^A-Za-z0-9]", "", tag.title())
    if problem_type == "simple_io":
        return f"class Main {{ static int solve{method}(int left, int right) {{ return Math.addExact(left, right) + {marker}; }} }}\n"
    if problem_type == "string_processing":
        return f"class Main {{ static int solve{method}(String text) {{ return (int) text.chars().filter(Character::isLetter).count() + {marker}; }} }}\n"
    return f"class Main {{ static int solve{method}(int[] values) {{ return java.util.Arrays.stream(values).filter(v -> v > 0).sum() + {marker}; }} }}\n"


def _label(case_type: str, ai_placeholder: bool) -> str:
    if ai_placeholder:
        return "UNCERTAIN"
    if case_type in {"INDEPENDENT_SOLUTION", "COMMON_STRUCTURE"}:
        return "INDEPENDENT"
    if case_type == "NATURAL_TEMPLATE":
        return "NATURAL_SIMILAR"
    if case_type == "HUMAN_REWRITE":
        return "SUSPICIOUS"
    return "TRANSFORMED"


def _provenance(case_type: str) -> dict[str, object]:
    if case_type == "AI_REWRITE":
        return {
            "source": "synthetic placeholder generated by deterministic seed builder; no AI model was invoked",
            "license_or_authorization": "project synthetic seed",
            "model_name": "NONE_PLACEHOLDER",
            "prompt_template": "NONE_PLACEHOLDER",
            "temperature": None,
            "generation_time": "2026-06-24T00:00:00Z",
            "manual_check_status": "PENDING",
            "functional_check_status": "NOT_RUN",
        }
    return {
        "source": "deterministic project synthetic seed builder",
        "license_or_authorization": "project synthetic seed",
        "manual_check_status": "VERIFIED",
        "functional_check_status": "NOT_RUN",
    }


def _rename(code: str, mapping: dict[str, str]) -> str:
    result = code
    for source, target in sorted(mapping.items(), key=lambda item: -len(item[0])):
        result = re.sub(rf"\b{re.escape(source)}\b", target, result)
    return result


def _sha256(code: str) -> str:
    return "sha256:" + hashlib.sha256(code.encode("utf-8")).hexdigest()


def main() -> int:
    payload = build_seed()
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "pairCount": len(payload["cases"]), "synthetic": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
