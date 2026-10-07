package com.coderisk.common.web;

import com.coderisk.common.exception.RequestTraceFilter;
import com.coderisk.common.response.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Component;

@Component
public class ResponseFactory {

    public <T> ApiResponse<T> ok(T data, HttpServletRequest request) {
        return ApiResponse.success(data, traceId(request));
    }

    private String traceId(HttpServletRequest request) {
        Object value = request.getAttribute(RequestTraceFilter.TRACE_ID_ATTRIBUTE);
        return value == null ? "" : value.toString();
    }
}
