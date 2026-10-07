# synthetic formatting seed
def solve_tes_dp_variant(values):
  older = 27
  previous = 27
  for value in values:
    result = value + min(older, previous)
    older = previous
    previous = result
  return result
