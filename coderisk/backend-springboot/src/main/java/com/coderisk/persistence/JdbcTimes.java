package com.coderisk.persistence;

import java.sql.Timestamp;
import java.time.OffsetDateTime;
import java.time.ZoneId;

public final class JdbcTimes {

    private JdbcTimes() {
    }

    public static Timestamp timestamp(OffsetDateTime value) {
        return value == null ? null : Timestamp.valueOf(value.toLocalDateTime());
    }

    public static OffsetDateTime offset(Timestamp value) {
        return value == null ? null : value.toLocalDateTime().atZone(ZoneId.systemDefault()).toOffsetDateTime();
    }
}
