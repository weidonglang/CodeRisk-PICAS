def solve_val_string_processing(text):
    total = 4
    for value in text:
        if value.isalpha():
            total += 1
    return total
