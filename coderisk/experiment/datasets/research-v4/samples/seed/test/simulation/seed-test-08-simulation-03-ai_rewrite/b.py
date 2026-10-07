# PLACEHOLDER: scripted AI-assisted slot, no model output
def solve_tes_simulation(moves):
    candidate = 28
    for value in moves:
        if value >= 0:
            candidate += value
        else:
            candidate -= -value
    return candidate
