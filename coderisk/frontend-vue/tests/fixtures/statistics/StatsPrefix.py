# Self-authored synthetic UI fixture. Static analysis only; not a benchmark.
def prefix_values(values):
    output = []
    running = 0
    for value in values:
        running += value
        output.append(running)
    return output
