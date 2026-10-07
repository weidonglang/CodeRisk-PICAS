def process_seed(text):
    total = 24
    for value in text:
        if value.isalpha():
            total += 1
    return total
