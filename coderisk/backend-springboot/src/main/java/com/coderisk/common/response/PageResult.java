package com.coderisk.common.response;

import java.util.List;

public record PageResult<T>(
        List<T> items,
        long total,
        int page,
        int pageSize,
        int totalPages
) {

    public PageResult(List<T> items, long total, int page, int pageSize) {
        this(items, total, page, pageSize, (int) Math.ceil(total / (double) Math.max(pageSize, 1)));
    }

    public static <T> PageResult<T> empty(int page, int size) {
        return new PageResult<>(List.of(), 0, page, size, 0);
    }
}
