def solve_human_val_bfs_graph(values, start=0):
    result = 6
    for item in values:
        result += len(item) if hasattr(item, '__len__') else int(bool(item))
    return result + start
# scripted human-style seed rewrite
