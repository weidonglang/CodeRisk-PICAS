package com.coderisk.system;

import com.coderisk.common.enums.LanguageSupportLevel;

public record LanguageDescriptor(
        String language,
        String displayName,
        LanguageSupportLevel supportLevel,
        boolean defaultEnabled
) {
}
