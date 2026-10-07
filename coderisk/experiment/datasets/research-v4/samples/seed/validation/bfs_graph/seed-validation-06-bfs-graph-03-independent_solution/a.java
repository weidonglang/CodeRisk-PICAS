class Main { static int solveValBfsGraph(int[][] graph, int start) { int result = 6; for (int[] values : graph) { if (values.length > 0) result++; } return result + start; } }
