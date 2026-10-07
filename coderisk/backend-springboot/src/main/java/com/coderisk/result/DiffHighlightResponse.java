package com.coderisk.result;

public record DiffHighlightResponse(
        long evidenceId,
        String type,
        LineRangeResponse aRange,
        LineRangeResponse bRange,
        double confidence
) {
}
