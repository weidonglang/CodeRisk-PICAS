package com.coderisk.experiment;

import com.coderisk.common.config.CoderiskProperties;
import com.coderisk.common.exception.ApiException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
public class ExperimentArtifactService {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final Path experimentsRoot;
    private final ObjectMapper objectMapper;

    public ExperimentArtifactService(CoderiskProperties properties, ObjectMapper objectMapper) {
        this.experimentsRoot = Path.of(properties.artifacts().rootPath())
                .toAbsolutePath()
                .normalize()
                .resolve("experiments");
        this.objectMapper = objectMapper;
    }

    public Map<String, Object> latest() {
        try {
            Path latestPath = experimentsRoot.resolve("latest.json").normalize();
            if (!Files.isRegularFile(latestPath)) {
                throw new ApiException(HttpStatus.NOT_FOUND, "EXPERIMENT_NOT_FOUND", "No experiment run has been published yet");
            }
            Map<String, Object> pointer = objectMapper.readValue(latestPath.toFile(), MAP_TYPE);
            String runId = String.valueOf(pointer.get("runId"));
            if (!runId.matches("[A-Za-z0-9._-]+")) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "EXPERIMENT_PATH_INVALID", "Invalid experiment run id");
            }
            Path runDirectory = experimentsRoot.resolve(runId).normalize();
            if (!runDirectory.startsWith(experimentsRoot)) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "EXPERIMENT_PATH_INVALID", "Experiment path escapes artifact root");
            }
            Map<String, Object> summary = objectMapper.readValue(runDirectory.resolve("metrics_summary.json").toFile(), MAP_TYPE);
            Map<String, Object> response = new LinkedHashMap<>();
            response.put("runId", runId);
            response.put("summary", summary);
            response.put("reportFile", runDirectory.resolve("experiment_report.md").toString().replace('\\', '/'));
            return Map.copyOf(response);
        } catch (ApiException exception) {
            throw exception;
        } catch (Exception exception) {
            throw new ApiException(HttpStatus.INTERNAL_SERVER_ERROR, "EXPERIMENT_READ_FAILED", "Failed to read experiment artifacts");
        }
    }
}
