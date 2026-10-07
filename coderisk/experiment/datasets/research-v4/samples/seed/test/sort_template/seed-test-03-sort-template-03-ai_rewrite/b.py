# PLACEHOLDER: scripted AI-assisted slot, no model output
def solve_tes_sort_template(values):
    candidate = list(values)
    for index in range(1, len(candidate)):
        value = candidate[index]
        cursor = index - 1
        while cursor >= 0 and candidate[cursor] > value:
            candidate[cursor + 1] = candidate[cursor]
            cursor -= 1
        candidate[cursor + 1] = value
    return candidate
