class Main {
    int value = 9;
    int fold() {
        int first = value;
        int value = 2;
        return first + value + this.value;
    }
}
