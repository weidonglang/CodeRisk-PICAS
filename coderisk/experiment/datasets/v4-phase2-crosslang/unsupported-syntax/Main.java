import java.util.Arrays;

class Main {
    static int sumPositive(int[] values) {
        return Arrays.stream(values).filter(value -> value > 0).sum();
    }
}
