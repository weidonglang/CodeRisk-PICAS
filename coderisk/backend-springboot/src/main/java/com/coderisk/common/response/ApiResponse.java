package com.coderisk.common.response;

import java.time.OffsetDateTime;

public record ApiResponse<T>(
        boolean success,
        String code,
        String message,
        T data,
        String traceId,
        OffsetDateTime timestamp
) {

    public static <T> ApiResponse<T> success(T data, String traceId) {
        return new ApiResponse<>(true, "OK", "success", data, traceId, OffsetDateTime.now());
    }

    public static <T> ApiResponse<T> failure(String code, String message, String traceId) {
        return new ApiResponse<>(false, code, message, null, traceId, OffsetDateTime.now());
    }
}
