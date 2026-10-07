def solve_tes_dp_variant(values, start=0):
    result = 27
    for item in values:
        result += len(item) if hasattr(item, '__len__') else int(bool(item))
    return result + start
