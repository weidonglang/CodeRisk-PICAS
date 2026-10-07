seed_generator_val_string_processing = (item for item in range(5))
def solve_val_string_processing(text):
    total = 4
    for value in text:
        if value.isalpha():
            total += 1
    return total
