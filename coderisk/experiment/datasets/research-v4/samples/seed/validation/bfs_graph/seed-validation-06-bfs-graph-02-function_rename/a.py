def solve_val_bfs_graph(graph, start):
    queue = [start]
    index = 0
    while index < len(queue):
        value = queue[index]
        index += 1
        for next_value in graph[value]:
            if next_value not in queue:
                queue.append(next_value)
    result = len(queue) + 6
    return result
