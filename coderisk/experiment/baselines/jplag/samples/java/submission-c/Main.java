class Main {
    static String reverse(String text) {
        StringBuilder builder = new StringBuilder();
        for (int index = text.length() - 1; index >= 0; index--) {
            builder.append(text.charAt(index));
        }
        return builder.toString();
    }
}
