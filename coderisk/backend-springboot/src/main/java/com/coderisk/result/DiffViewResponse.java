package com.coderisk.result;

import java.util.List;

public record DiffViewResponse(
        long resultId,
        long taskId,
        CodeSideResponse codeA,
        CodeSideResponse codeB,
        List<DiffHighlightResponse> highlights
) {
}
