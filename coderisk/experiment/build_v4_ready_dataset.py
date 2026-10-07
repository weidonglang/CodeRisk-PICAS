from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiment" / "datasets" / "v4-ready" / "cases.json"
DATASET_VERSION = "coderisk-v4-ready-synthetic-1.0"


def rename(code: str, mapping: dict[str, str]) -> str:
    result = code
    for source, target in sorted(mapping.items(), key=lambda item: -len(item[0])):
        result = re.sub(rf"\b{re.escape(source)}\b", target, result)
    return result


def formatted(code: str) -> str:
    lines = code.rstrip().splitlines()
    return "# formatting-only synthetic variant\n\n" + "\n".join(line.rstrip() for line in lines) + "\n"


FAMILIES = [
    {
        "problem_type": "simple_io",
        "problem_group": "G1",
        "title": "Pair sum",
        "description": "Read two integers and output their sum. The solution space is intentionally small.",
        "input_format": "two integers",
        "output_format": "their sum",
        "constraints_text": "-1000 <= a,b <= 1000",
        "base": "def solve(left, right):\n    result = left + right\n    return result\n",
        "natural": "def solve(left, right):\n    result = left + right + 0\n    return result\n",
        "independent": "def solve(left, right):\n    return sum((left, right))\n",
        "rename_type": "PARAMETER_RENAME",
        "rename_map": {"left": "first", "right": "second", "result": "answer"},
        "test_map": {"solve": "calculate", "left": "x", "right": "y", "result": "total"},
        "test_rename_map": {"x": "first_value", "y": "second_value", "total": "answer"},
    },
    {
        "problem_type": "array_loop",
        "problem_group": "G2",
        "title": "Positive array sum",
        "description": "Sum all positive values in an integer array using a loop or an equivalent expression.",
        "input_format": "n and n integers",
        "output_format": "positive sum",
        "constraints_text": "1 <= n <= 10000",
        "base": "def solve(values):\n    total = 0\n    for value in values:\n        if value > 0:\n            total += value\n    return total\n",
        "natural": "def solve(values):\n    total = 0\n    for value in values:\n        if 0 < value:\n            total = total + value\n    return total\n",
        "independent": "def solve(values):\n    return sum(filter(lambda item: item > 0, values))\n",
        "rename_type": "VARIABLE_RENAME",
        "rename_map": {"values": "numbers", "total": "answer", "value": "item"},
        "test_map": {"solve": "aggregate", "values": "items", "total": "acc", "value": "current"},
        "test_rename_map": {"items": "numbers", "acc": "result", "current": "element"},
    },
    {
        "problem_type": "sort_template",
        "problem_group": "G3",
        "title": "Insertion sort",
        "description": "Sort a list of integers. Standard sorting templates create a measurable natural similarity risk.",
        "input_format": "n and n integers",
        "output_format": "sorted integers",
        "constraints_text": "1 <= n <= 2000",
        "base": "def insertion_sort(values):\n    result = list(values)\n    for index in range(1, len(result)):\n        current = result[index]\n        position = index - 1\n        while position >= 0 and result[position] > current:\n            result[position + 1] = result[position]\n            position -= 1\n        result[position + 1] = current\n    return result\n",
        "natural": "def insertion_sort(values):\n    result = list(values)\n    for index in range(1, len(result)):\n        current = result[index]\n        position = index - 1\n        while position >= 0 and result[position] > current:\n            result[position + 1] = result[position]\n            position = position - 1\n        result[position + 1] = current\n    return result\n",
        "independent": "def insertion_sort(values):\n    return sorted(values)\n",
        "rename_type": "FUNCTION_RENAME",
        "rename_map": {"insertion_sort": "order_values", "result": "data", "index": "i", "current": "key", "position": "j"},
        "test_map": {"insertion_sort": "sort_items", "values": "items", "result": "buffer", "index": "idx", "current": "pivot", "position": "cursor"},
        "test_rename_map": {"sort_items": "arrange", "items": "numbers", "buffer": "data", "idx": "i", "pivot": "key", "cursor": "j"},
    },
    {
        "problem_type": "dfs_graph",
        "problem_group": "G3",
        "title": "Graph reachability",
        "description": "Return the vertices reachable from a start vertex in an adjacency-list graph.",
        "input_format": "graph and start vertex",
        "output_format": "reachable set",
        "constraints_text": "1 <= vertices <= 200000",
        "base": "def reachable(graph, start):\n    seen = {start}\n    stack = [start]\n    while stack:\n        node = stack.pop()\n        for neighbor in graph[node]:\n            if neighbor not in seen:\n                seen.add(neighbor)\n                stack.append(neighbor)\n    return seen\n",
        "natural": "def reachable(graph, start):\n    seen = {start}\n    stack = [start]\n    while stack:\n        node = stack.pop()\n        for neighbor in list(graph[node]):\n            if neighbor not in seen:\n                seen.add(neighbor)\n                stack.append(neighbor)\n    return seen\n",
        "independent": "def reachable(graph, start):\n    def visit(node, seen):\n        if node in seen:\n            return\n        seen.add(node)\n        for neighbor in graph[node]:\n            visit(neighbor, seen)\n    result = set()\n    visit(start, result)\n    return result\n",
        "rename_type": "PARAMETER_RENAME",
        "rename_map": {"graph": "edges", "start": "source", "seen": "visited", "stack": "pending", "node": "vertex", "neighbor": "next_vertex"},
        "test_map": {"reachable": "walk", "graph": "adjacency", "start": "origin", "seen": "known", "stack": "todo", "node": "current", "neighbor": "next_node"},
        "test_rename_map": {"adjacency": "edges", "origin": "source", "known": "visited", "todo": "pending", "current": "vertex", "next_node": "neighbor"},
    },
    {
        "problem_type": "dp_variant",
        "problem_group": "G4",
        "title": "Minimum climbing cost",
        "description": "Compute the minimum accumulated cost to move beyond the final stair using one- or two-step transitions.",
        "input_format": "n and costs",
        "output_format": "minimum cost",
        "constraints_text": "2 <= n <= 100000",
        "base": "def min_cost(costs):\n    previous_two = 0\n    previous_one = 0\n    for cost in costs:\n        current = cost + min(previous_one, previous_two)\n        previous_two = previous_one\n        previous_one = current\n    return min(previous_one, previous_two)\n",
        "natural": "def min_cost(costs):\n    previous_two = 0\n    previous_one = 0\n    for cost in costs:\n        current = min(previous_one, previous_two) + cost\n        previous_two = previous_one\n        previous_one = current\n    return min(previous_two, previous_one)\n",
        "independent": "def min_cost(costs):\n    from functools import lru_cache\n    @lru_cache(None)\n    def solve(index):\n        if index >= len(costs):\n            return 0\n        return costs[index] + min(solve(index + 1), solve(index + 2))\n    return min(solve(0), solve(1))\n",
        "rename_type": "VARIABLE_RENAME",
        "rename_map": {"min_cost": "minimum_fee", "costs": "fees", "previous_two": "older", "previous_one": "prior", "cost": "fee", "current": "candidate"},
        "test_map": {"min_cost": "climb", "costs": "prices", "previous_two": "two_back", "previous_one": "one_back", "cost": "price", "current": "best"},
        "test_rename_map": {"climb": "minimum_cost", "prices": "fees", "two_back": "older", "one_back": "prior", "price": "fee", "best": "candidate"},
    },
]


def build_case(
    family: dict[str, object],
    split: str,
    suffix: str,
    experiment_label: str,
    case_type: str,
    code_a: str,
    code_b: str,
) -> dict[str, object]:
    problem_id = f"{split.upper()}-{str(family['problem_type']).upper().replace('_', '-')}-01"
    return {
        "case_id": f"{problem_id}-{suffix}",
        "problem_id": problem_id,
        "problem_type": family["problem_type"],
        "problem_group": family["problem_group"],
        "split": split,
        "source_id": f"SRC-{problem_id}",
        "experiment_label": experiment_label,
        "case_type": case_type,
        "language": "python",
        "dataset_version": DATASET_VERSION,
        "question": {
            "title": family["title"],
            "description": family["description"],
            "input_format": family["input_format"],
            "output_format": family["output_format"],
            "constraints_text": family["constraints_text"],
        },
        "code_a": code_a,
        "code_b": code_b,
    }


def build_dataset() -> dict[str, object]:
    cases: list[dict[str, object]] = []
    for family in FAMILIES:
        for split in ("validation", "test"):
            base = str(family["base"])
            natural = str(family["natural"])
            independent = str(family["independent"])
            if split == "validation":
                transformed = rename(base, dict(family["rename_map"]))
            else:
                base_mapping = dict(family["test_map"])
                base = rename(base, base_mapping)
                natural = rename(natural, base_mapping)
                independent = rename(independent, base_mapping)
                transformed = rename(base, dict(family["test_rename_map"]))

            cases.extend(
                [
                    build_case(family, split, "RENAME", "TRANSFORMED", str(family["rename_type"]), base, transformed),
                    build_case(family, split, "NATURAL", "NATURAL_SIMILAR", "NATURAL_TEMPLATE", base, natural),
                    build_case(family, split, "INDEPENDENT", "INDEPENDENT", "INDEPENDENT_SOLUTION", base, independent),
                ]
            )
            if split == "test":
                cases.append(
                    build_case(
                        family,
                        split,
                        "SUSPICIOUS-FORMAT",
                        "SUSPICIOUS",
                        "FORMAT_COMMENT_CHANGE",
                        base,
                        formatted(transformed),
                    )
                )

    parser_family = FAMILIES[1]
    cases.append(
        build_case(
            parser_family,
            "test",
            "PARSER-FALLBACK",
            "UNCERTAIN",
            "FORMAT_COMMENT_CHANGE",
            "def broken(:\n    return 1\n",
            "def solve(values):\n    return sum(values)\n",
        )
    )
    return {
        "dataset_id": "coderisk-v4-ready-synthetic",
        "dataset_version": DATASET_VERSION,
        "description": "Problem-level split synthetic dataset for the V4 readiness gate. No real student submissions.",
        "license": "Project synthetic test data",
        "cases": cases,
    }


def main() -> int:
    dataset = build_dataset()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "caseCount": len(dataset["cases"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
