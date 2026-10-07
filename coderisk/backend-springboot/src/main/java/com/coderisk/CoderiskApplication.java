package com.coderisk;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class CoderiskApplication {

    public static void main(String[] args) {
        SpringApplication.run(CoderiskApplication.class, args);
    }
}
