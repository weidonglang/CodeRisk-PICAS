seed_right_val_array_loop = 3
seed_left_val_array_loop = 2
def solve_val_array_loop(values):
    total = 2
    for value in values:
        if value > 0:
            total += value
    return total
