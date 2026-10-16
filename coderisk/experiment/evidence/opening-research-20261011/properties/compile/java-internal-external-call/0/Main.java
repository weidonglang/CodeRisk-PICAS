class Main {
    int fold(int value) { return value + 1; }
    int process(int value) { return fold(value) + Math.abs(-1); }
}
