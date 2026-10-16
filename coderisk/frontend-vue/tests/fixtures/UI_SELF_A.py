# Self-authored UI fixture. Uploaded for static analysis; never executed by the test.
def total(numbers):
    result = 0
    for number in numbers:
        result += number
    return result


size = int(input())
values = list(map(int, input().split()))
print(total(values[:size]))
