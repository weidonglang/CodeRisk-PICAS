class Main { static int solveValDfsGraph(int[][] graph, int start) { int result = 5; for (int[] values : graph) { if (values.length > 0) result++; } return result + start; } }
