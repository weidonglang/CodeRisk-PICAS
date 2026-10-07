from collections import deque

def distance(graph, start, target):
    dist = [0] * len(graph)
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node == target:
            return dist[node]
        for next_node in graph[node]:
            if dist[next_node] == 0:
                dist[next_node] = dist[node] + 1
                queue.append(next_node)
    return -1
