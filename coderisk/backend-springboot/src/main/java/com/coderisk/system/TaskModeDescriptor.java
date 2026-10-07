package com.coderisk.system;

public record TaskModeDescriptor(
        String code,
        String name,
        String version,
        boolean stable
) {
}
