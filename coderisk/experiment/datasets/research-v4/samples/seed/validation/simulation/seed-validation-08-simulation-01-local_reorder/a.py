def solve_val_simulation(moves):
    result = 8
    for value in moves:
        if value >= 0:
            result += value
        else:
            result -= -value
    return result
