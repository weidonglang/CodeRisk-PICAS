class Main {
    static int positiveTotal(int[] numbers) {
        int result = 0;
        for (int number : numbers) {
            if (number > 0) {
                result++;
            }
        }
        return result;
    }
}
