# Self-authored synthetic UI fixture. Static analysis only; not a benchmark.
def count_values(values):
    frequencies = {}
    for value in values:
        if value in frequencies:
            frequencies[value] += 1
        else:
            frequencies[value] = 1
    return frequencies
