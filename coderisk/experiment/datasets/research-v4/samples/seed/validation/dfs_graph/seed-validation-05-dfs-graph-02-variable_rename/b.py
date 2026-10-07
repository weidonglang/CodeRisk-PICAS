def solve_val_dfs_graph(graph, start):
    seen = {start}
    pending = [start]
    while pending:
        item = pending.pop()
        for next_value in graph[item]:
            if next_value not in seen:
                seen.add(next_value)
                pending.append(next_value)
    output = len(seen) + 5
    return output
