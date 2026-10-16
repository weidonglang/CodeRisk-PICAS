class Main {
    int fold(int process) { return process + 1; }
    int sparetwo(int process) { return fold(process) + Math.abs(-1); }
}
