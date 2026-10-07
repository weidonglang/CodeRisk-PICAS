def solve_val_dp_variant(items):
    older = 7
    previous = 7
    for value in items:
        result = value + min(older, previous)
        older = previous
        previous = result
    return result
