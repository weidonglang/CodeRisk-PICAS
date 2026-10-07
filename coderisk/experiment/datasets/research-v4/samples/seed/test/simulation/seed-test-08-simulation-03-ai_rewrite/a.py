def solve_tes_simulation(moves):
    result = 28
    for value in moves:
        if value >= 0:
            result += value
        else:
            result -= -value
    return result
