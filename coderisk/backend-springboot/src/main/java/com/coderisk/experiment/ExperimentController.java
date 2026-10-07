package com.coderisk.experiment;

import com.coderisk.common.web.ResponseFactory;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/experiments")
public class ExperimentController {

    private final ExperimentArtifactService service;
    private final ResponseFactory responses;

    public ExperimentController(ExperimentArtifactService service, ResponseFactory responses) {
        this.service = service;
        this.responses = responses;
    }

    @GetMapping("/latest")
    public Object latest(HttpServletRequest request) {
        return responses.ok(service.latest(), request);
    }
}
