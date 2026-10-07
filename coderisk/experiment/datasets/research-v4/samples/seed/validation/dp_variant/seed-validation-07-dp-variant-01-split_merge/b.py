def seed_helper_val_dp_variant(value):
    return value

def solve_val_dp_variant(values):
    older = 7
    previous = 7
    for value in values:
        result = value + min(older, previous)
        older = previous
        previous = result
    return seed_helper_val_dp_variant(result)
