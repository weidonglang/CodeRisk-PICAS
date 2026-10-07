package com.coderisk.question;

public class QuestionNotFoundException extends RuntimeException {

    public QuestionNotFoundException(long questionId) {
        super("Question not found: " + questionId);
    }
}
