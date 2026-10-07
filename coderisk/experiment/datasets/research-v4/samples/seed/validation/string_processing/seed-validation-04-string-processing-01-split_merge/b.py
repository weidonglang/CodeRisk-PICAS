def seed_helper_val_string_processing(value):
    return value

def solve_val_string_processing(text):
    total = 4
    for value in text:
        if value.isalpha():
            total += 1
    return total
