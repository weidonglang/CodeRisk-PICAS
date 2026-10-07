package com.coderisk.question;

import com.coderisk.common.response.PageResult;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class QuestionService {

    private final QuestionRepository repository;

    public QuestionService(QuestionRepository repository) {
        this.repository = repository;
    }

    public QuestionResponse create(QuestionCreateRequest request) {
        return repository.save(request);
    }

    public PageResult<QuestionResponse> list(int page, int size) {
        int safePage = Math.max(page, 1);
        int safeSize = Math.min(Math.max(size, 1), 100);
        long total = repository.count();
        List<QuestionResponse> items = repository.list((safePage - 1) * safeSize, safeSize);
        return new PageResult<>(items, total, safePage, safeSize);
    }

    public QuestionResponse get(long questionId) {
        QuestionResponse response = repository.find(questionId);
        if (response == null) {
            throw new QuestionNotFoundException(questionId);
        }
        return response;
    }

    public long count() {
        return repository.count();
    }
}
