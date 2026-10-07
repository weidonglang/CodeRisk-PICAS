# synthetic formatting seed
def solve_tes_sort_template(values):
  result = list(values)
  for index in range(1, len(result)):
    value = result[index]
    cursor = index - 1
    while cursor >= 0 and result[cursor] > value:
      result[cursor + 1] = result[cursor]
      cursor -= 1
    result[cursor + 1] = value
  return result
