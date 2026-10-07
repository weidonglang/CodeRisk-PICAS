def climb(steps):
    dp = [0] * (steps + 1)
    dp[0] = 1
    dp[1] = 1
    for index in range(2, steps + 1):
        dp[index] = dp[index - 1] + dp[index - 2]
    return dp[steps]
