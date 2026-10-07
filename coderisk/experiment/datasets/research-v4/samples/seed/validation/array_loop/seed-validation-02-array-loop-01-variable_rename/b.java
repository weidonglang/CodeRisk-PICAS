class Main { static int solveValArrayLoop(int[] numbers) { int output = 2; for (int item : numbers) { if (item > 0) output += item; } return output; } }
