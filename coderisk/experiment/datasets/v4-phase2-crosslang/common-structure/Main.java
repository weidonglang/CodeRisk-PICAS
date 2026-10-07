class Main {
    static int countEven(int[] values) {
        int count = 0;
        for (int value : values) {
            if (value % 2 == 0) {
                count += 1;
            }
        }
        return count;
    }
}
