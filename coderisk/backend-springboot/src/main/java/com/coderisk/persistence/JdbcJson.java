package com.coderisk.persistence;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class JdbcJson {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final ObjectMapper objectMapper;

    public JdbcJson(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public String write(Object value) {
        try {
            return objectMapper.writeValueAsString(value == null ? Map.of() : value);
        } catch (Exception exception) {
            throw new IllegalStateException("Failed to serialize database JSON", exception);
        }
    }

    public Map<String, Object> readMap(String value) {
        if (value == null || value.isBlank()) {
            return Map.of();
        }
        try {
            Object decoded = objectMapper.readValue(value, Object.class);
            if (decoded instanceof String nested) {
                decoded = objectMapper.readValue(nested, Object.class);
            }
            return objectMapper.convertValue(decoded, MAP_TYPE);
        } catch (Exception exception) {
            throw new IllegalStateException("Failed to deserialize database JSON", exception);
        }
    }
}
