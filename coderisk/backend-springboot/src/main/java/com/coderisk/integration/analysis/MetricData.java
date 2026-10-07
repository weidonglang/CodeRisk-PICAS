package com.coderisk.integration.analysis;

public record MetricData(
        String name,
        double value,
        double weight,
        String explanation
) {
}
