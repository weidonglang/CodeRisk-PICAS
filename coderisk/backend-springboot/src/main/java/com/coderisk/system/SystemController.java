package com.coderisk.system;

import com.coderisk.common.config.CoderiskProperties;
import com.coderisk.common.enums.LanguageSupportLevel;
import com.coderisk.common.web.ResponseFactory;
import jakarta.servlet.http.HttpServletRequest;
import java.time.OffsetDateTime;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/system")
public class SystemController {

    private final CoderiskProperties properties;
    private final ResponseFactory responses;

    public SystemController(CoderiskProperties properties, ResponseFactory responses) {
        this.properties = properties;
        this.responses = responses;
    }

    @GetMapping("/health")
    public Object health(HttpServletRequest request) {
        SystemHealth health = new SystemHealth(
                "UP",
                properties.appVersion(),
                "coderisk-backend",
                OffsetDateTime.now(),
                properties.analysis().baseUrl()
        );
        return responses.ok(health, request);
    }

    @GetMapping("/languages")
    public Object languages(HttpServletRequest request) {
        List<LanguageDescriptor> languages = List.of(
                new LanguageDescriptor("java", "Java", LanguageSupportLevel.STABLE, true),
                new LanguageDescriptor("python", "Python", LanguageSupportLevel.STABLE, true),
                new LanguageDescriptor("c", "C", LanguageSupportLevel.EXPERIMENTAL, false)
        );
        return responses.ok(languages, request);
    }

    @GetMapping("/task-modes")
    public Object taskModes(HttpServletRequest request) {
        List<TaskModeDescriptor> modes = List.of(
                new TaskModeDescriptor("BASIC_TOKEN", "基础 Token 检测", "V1", true),
                new TaskModeDescriptor("TOKEN_AST", "Token + 基础 AST 检测", "V1", true),
                new TaskModeDescriptor("PICAS_INVARIANT", "置换不变规范化检测", "V1.5", true),
                new TaskModeDescriptor("PICAS_STANDARD", "PICAS 标准检测", "V2", true),
                new TaskModeDescriptor("PICAS_CROSSLANG", "跨语言 IR + 轻量摘要（实验性）", "V4 Phase 1-2", false),
                new TaskModeDescriptor("PICAS_EXPERIMENTAL", "实验/消融检测", "V3/V4", false)
        );
        return responses.ok(modes, request);
    }
}
