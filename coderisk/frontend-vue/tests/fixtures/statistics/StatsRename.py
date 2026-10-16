# Self-authored synthetic UI fixture. Static analysis only; not a benchmark.
def accumulate(items):
    answer = 0
    for item in items:
        answer += item
    return answer
