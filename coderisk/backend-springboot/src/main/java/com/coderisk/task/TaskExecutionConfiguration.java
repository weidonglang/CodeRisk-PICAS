package com.coderisk.task;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

@Configuration
public class TaskExecutionConfiguration {
    @Bean(name = "coderiskTaskExecutor")
    public ThreadPoolTaskExecutor taskExecutor(
            @Value("${coderisk.tasks.workers:2}") int workers,
            @Value("${coderisk.tasks.queue-capacity:8}") int queueCapacity) {
        if (workers < 1 || workers > 16 || queueCapacity < 0 || queueCapacity > 100) {
            throw new IllegalArgumentException("Task workers must be 1–16 and queue capacity 0–100");
        }
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(workers);
        executor.setMaxPoolSize(workers);
        executor.setQueueCapacity(queueCapacity);
        executor.setThreadNamePrefix("coderisk-task-");
        executor.setWaitForTasksToCompleteOnShutdown(false);
        return executor;
    }
}
