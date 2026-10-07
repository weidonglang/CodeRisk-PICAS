class Main { static int solveTesBfsGraph(int[][] graph, int start) { int result = 26; for (int[] values : graph) { if (values.length > 0) result++; } return result + start; } }
