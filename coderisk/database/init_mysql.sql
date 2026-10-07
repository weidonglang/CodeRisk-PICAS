CREATE DATABASE IF NOT EXISTS coderisk
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

CREATE USER IF NOT EXISTS 'coderisk'@'localhost' IDENTIFIED BY 'coderisk';
CREATE USER IF NOT EXISTS 'coderisk'@'%' IDENTIFIED BY 'coderisk';

-- Local development only: make reruns deterministic when the account already exists.
ALTER USER 'coderisk'@'localhost' IDENTIFIED BY 'coderisk';
ALTER USER 'coderisk'@'%' IDENTIFIED BY 'coderisk';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES,
      CREATE VIEW, SHOW VIEW, TRIGGER, CREATE TEMPORARY TABLES, LOCK TABLES
ON coderisk.* TO 'coderisk'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES,
      CREATE VIEW, SHOW VIEW, TRIGGER, CREATE TEMPORARY TABLES, LOCK TABLES
ON coderisk.* TO 'coderisk'@'%';
FLUSH PRIVILEGES;
