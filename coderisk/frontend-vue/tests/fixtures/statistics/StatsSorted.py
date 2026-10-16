# Self-authored synthetic UI fixture. Static analysis only; not a benchmark.
def order_values(values):
    ordered = sorted(values)
    if len(ordered) == 0:
        return []
    return ordered
