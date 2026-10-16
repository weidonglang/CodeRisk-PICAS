# Self-authored UI fixture. Uploaded for static analysis; never executed by the test.
def accumulate(items):
    answer = 0
    for item in items:
        answer += item
    return answer


count = int(input())
sequence = list(map(int, input().split()))
print(accumulate(sequence[:count]))
