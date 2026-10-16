"""Descriptive paired component statistics; does not shadow the stdlib module."""
from __future__ import annotations

from collections import defaultdict
import math
import random
import statistics as stdstats


def percentile(values, probability):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def distribution(values, requested):
    present = [value for value in values if value is not None]
    if any(not math.isfinite(value) for value in present):
        raise ValueError("Nonfinite descriptive value")
    return {"n_requested": requested, "n_available": len(present), "n_missing": requested - len(present),
            "mean": stdstats.mean(present) if present else None, "median": percentile(present, .5),
            "p90": percentile(present, .9), "p95": percentile(present, .95), "quantile_rule": "LINEAR_TYPE_7"}


def paired_cluster_interval(rows, *, seed, replicates, minimum_clusters):
    if type(seed) is not int or type(replicates) is not int or not 100 <= replicates <= 5000 or type(minimum_clusters) is not int or minimum_clusters < 2:
        raise ValueError("Bounded replicates, seed and at least two clusters required")
    groups = defaultdict(list)
    for row in rows:
        if row.get("canonical") is not None and row.get("raw") is not None:
            groups[row["group_id"]].append(row["canonical"] - row["raw"])
    # One mean per connected component; a dense question does not receive n*(n-1)/2 weight.
    means = [stdstats.mean(values) for _, values in sorted(groups.items())]
    result = {"estimand": "COMPONENT_MACRO_CANONICAL_MINUS_RAW", "clusters": len(means),
              "point": stdstats.mean(means) if means else None, "interval95": None,
              "seed": seed, "replicates": replicates, "pair_bootstrap": False,
              "assumption": "Exchangeable connected problem/source/session components, not independent code pairs"}
    if len(means) < minimum_clusters:
        return {**result, "status": "NOT_ESTIMABLE_TOO_FEW_CONNECTED_CLUSTERS"}
    rng = random.Random(seed)
    draws = [stdstats.mean(rng.choices(means, k=len(means))) for _ in range(replicates)]
    return {**result, "interval95": [percentile(draws, .025), percentile(draws, .975)],
            "status": "DESCRIPTIVE_CLUSTER_BOOTSTRAP_NOT_CAUSAL_EVIDENCE"}
