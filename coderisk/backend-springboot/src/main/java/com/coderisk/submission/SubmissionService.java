package com.coderisk.submission;

import com.coderisk.common.config.CoderiskProperties;
import com.coderisk.common.enums.LanguageSupportLevel;
import com.coderisk.common.enums.ParserStatus;
import com.coderisk.common.exception.ApiException;
import com.coderisk.question.QuestionService;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class SubmissionService {

    private static final Map<String, String> EXTENSION_LANGUAGE = Map.of(
            ".java", "java",
            ".py", "python",
            ".c", "c",
            ".cpp", "cpp",
            ".html", "html",
            ".htm", "html"
    );

    private final QuestionService questionService;
    private final CoderiskProperties properties;
    private final SubmissionRepository repository;

    public SubmissionService(
            QuestionService questionService,
            CoderiskProperties properties,
            SubmissionRepository repository
    ) {
        this.questionService = questionService;
        this.properties = properties;
        this.repository = repository;
    }

    public SubmissionResponse store(long questionId, MultipartFile file, String studentId) {
        questionService.get(questionId);
        validateFile(file);
        String originalFileName = safeFileName(file.getOriginalFilename());
        String extension = extensionOf(originalFileName);
        String language = EXTENSION_LANGUAGE.get(extension);
        String storageKey = UUID.randomUUID().toString();
        Path target = rawCodePath(questionId, storageKey, extension);
        copyFile(file, target);
        return repository.save(
                questionId,
                normalizeStudentId(studentId, storageKey),
                language,
                supportLevel(language),
                originalFileName,
                file.getSize(),
                target.toString().replace('\\', '/'),
                sha256(target)
        );
    }

    public List<SubmissionResponse> listByQuestion(long questionId) {
        questionService.get(questionId);
        return repository.findByQuestion(questionId);
    }

    public SubmissionResponse get(long submissionId) {
        SubmissionResponse response = repository.find(submissionId);
        if (response == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "SUBMISSION_NOT_FOUND", "Submission not found: " + submissionId);
        }
        return response;
    }

    public List<SubmissionResponse> getAll(List<Long> submissionIds) {
        return submissionIds.stream().map(this::get).toList();
    }

    public long count() {
        return repository.count();
    }

    private void validateFile(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "FILE_EMPTY", "Uploaded file must not be empty");
        }
        long maxBytes = properties.upload().maxFileSizeMb() * 1024L * 1024L;
        if (file.getSize() > maxBytes) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "FILE_TOO_LARGE", "Uploaded file exceeds max size");
        }
        String extension = extensionOf(safeFileName(file.getOriginalFilename()));
        List<String> allowed = properties.upload().allowedExtensions() == null
                ? List.of()
                : properties.upload().allowedExtensions();
        boolean allowedExtension = allowed.stream()
                .map(value -> value.toLowerCase(Locale.ROOT))
                .anyMatch(value -> value.equals(extension));
        if (!allowedExtension || !EXTENSION_LANGUAGE.containsKey(extension)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "FILE_TYPE_NOT_SUPPORTED", "Unsupported file type: " + extension);
        }
    }

    private Path rawCodePath(long questionId, String storageKey, String extension) {
        Path uploadRoot = Path.of(properties.upload().rootPath()).toAbsolutePath().normalize();
        Path target = uploadRoot
                .resolve("submissions")
                .resolve(String.valueOf(questionId))
                .resolve(storageKey)
                .resolve("raw" + extension)
                .normalize();
        if (!target.startsWith(uploadRoot)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "FILE_PATH_INVALID", "Upload path escapes root directory");
        }
        return target;
    }

    private void copyFile(MultipartFile file, Path target) {
        try {
            Files.createDirectories(target.getParent());
            try (InputStream input = file.getInputStream()) {
                Files.copy(input, target, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException exception) {
            throw new ApiException(HttpStatus.INTERNAL_SERVER_ERROR, "FILE_STORAGE_FAILED", exception.getMessage());
        }
    }

    private String safeFileName(String originalFileName) {
        if (originalFileName == null || originalFileName.isBlank()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "FILE_NAME_INVALID", "Uploaded file name is required");
        }
        return Path.of(originalFileName).getFileName().toString();
    }

    private String extensionOf(String fileName) {
        int index = fileName.lastIndexOf('.');
        if (index < 0) {
            return "";
        }
        return fileName.substring(index).toLowerCase(Locale.ROOT);
    }

    private LanguageSupportLevel supportLevel(String language) {
        return List.of("c", "html", "cpp").contains(language) ? LanguageSupportLevel.EXPERIMENTAL : LanguageSupportLevel.STABLE;
    }

    private String normalizeStudentId(String studentId, String storageKey) {
        if (studentId == null || studentId.isBlank()) {
            return "anonymous-" + storageKey.substring(0, 8);
        }
        return studentId.trim();
    }

    private String sha256(Path path) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (InputStream input = Files.newInputStream(path)) {
                byte[] buffer = new byte[8192];
                int read;
                while ((read = input.read(buffer)) >= 0) {
                    digest.update(buffer, 0, read);
                }
            }
            return "sha256:" + HexFormat.of().formatHex(digest.digest());
        } catch (IOException | NoSuchAlgorithmException exception) {
            throw new ApiException(HttpStatus.INTERNAL_SERVER_ERROR, "FILE_HASH_FAILED", "Failed to hash uploaded file");
        }
    }
}
