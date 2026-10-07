def solve_human_tes_dfs_graph(values, start=0):
    result = 25
    for item in values:
        result += len(item) if hasattr(item, '__len__') else int(bool(item))
    return result + start
# scripted human-style seed rewrite
