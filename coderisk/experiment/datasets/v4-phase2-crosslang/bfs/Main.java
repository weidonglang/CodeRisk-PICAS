import java.util.ArrayDeque;

class Main {
    static int distance(int[][] graph, int start, int target) {
        int[] dist = new int[graph.length];
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        queue.add(start);
        while (!queue.isEmpty()) {
            int node = queue.remove();
            if (node == target) {
                return dist[node];
            }
            for (int next : graph[node]) {
                if (dist[next] == 0) {
                    dist[next] = dist[node] + 1;
                    queue.add(next);
                }
            }
        }
        return -1;
    }
}
