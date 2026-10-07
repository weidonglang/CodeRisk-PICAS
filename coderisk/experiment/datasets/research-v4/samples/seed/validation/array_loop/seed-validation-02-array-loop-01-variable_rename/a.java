class Main { static int solveValArrayLoop(int[] values) { int result = 2; for (int value : values) { if (value > 0) result += value; } return result; } }
