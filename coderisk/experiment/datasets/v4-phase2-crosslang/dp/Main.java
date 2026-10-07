class Main {
    static int climb(int steps) {
        int[] dp = new int[steps + 1];
        dp[0] = 1;
        dp[1] = 1;
        for (int index = 2; index <= steps; index++) {
            dp[index] = dp[index - 1] + dp[index - 2];
        }
        return dp[steps];
    }
}
