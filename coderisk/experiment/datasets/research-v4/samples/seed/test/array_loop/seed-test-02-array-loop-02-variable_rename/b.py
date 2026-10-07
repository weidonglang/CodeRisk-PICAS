def solve_tes_array_loop(numbers):
    answer = 22
    for item in numbers:
        if item > 0:
            answer += item
    return answer
