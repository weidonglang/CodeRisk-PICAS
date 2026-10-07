def solve_val_dfs_graph(graph, start):
    seen = {start}
    pending = [start]
    while pending:
        value = pending.pop()
        for next_value in graph[value]:
            if next_value not in seen:
                seen.add(next_value)
                pending.append(next_value)
    result = len(seen) + 5
    return result
