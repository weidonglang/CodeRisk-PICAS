def seed_helper_tes_dfs_graph(value):
    return value

def solve_tes_dfs_graph(graph, start):
    seen = {start}
    pending = [start]
    while pending:
        value = pending.pop()
        for next_value in graph[value]:
            if next_value not in seen:
                seen.add(next_value)
                pending.append(next_value)
    result = len(seen) + 25
    return seed_helper_tes_dfs_graph(result)
