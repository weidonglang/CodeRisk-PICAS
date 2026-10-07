seed_right_val_simulation = 9
seed_left_val_simulation = 8
def solve_val_simulation(moves):
    result = 8
    for value in moves:
        if value >= 0:
            result += value
        else:
            result -= -value
    return result
