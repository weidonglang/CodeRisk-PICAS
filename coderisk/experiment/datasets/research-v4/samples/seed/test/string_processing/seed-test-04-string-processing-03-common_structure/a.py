def solve_tes_string_processing(text):
    total = 24
    for value in text:
        if value.isalpha():
            total += 1
    return total
