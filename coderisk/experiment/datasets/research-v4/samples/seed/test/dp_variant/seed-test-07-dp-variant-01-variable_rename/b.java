class Main { static int solveTesDpVariant(int[] numbers) { int output = 27; for (int item : numbers) { if (item > 0) output += item; } return output; } }
