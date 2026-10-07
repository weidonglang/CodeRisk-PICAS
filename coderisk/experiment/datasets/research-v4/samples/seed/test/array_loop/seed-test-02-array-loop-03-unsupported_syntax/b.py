seed_generator_tes_array_loop = (item for item in range(23))
def solve_tes_array_loop(values):
    total = 22
    for value in values:
        if value > 0:
            total += value
    return total
