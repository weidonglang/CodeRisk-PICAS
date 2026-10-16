def maximum(values):
    best = values[0]
    for item in values:
        if item > best:
            best = item
    return best
