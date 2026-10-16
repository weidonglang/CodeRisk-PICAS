# Self-authored synthetic UI fixture. Static analysis only; not a benchmark.
def largest_value(values):
    if not values:
        return None
    best = values[0]
    for current in values:
        if current > best:
            best = current
    return best
