def sum_large(values):
    total = 0
    for value in values:
        if value > 100:
            total += value
    return total
