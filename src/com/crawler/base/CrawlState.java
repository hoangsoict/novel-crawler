package com.crawler.base;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;

public class CrawlState {
    private static final String KEY_LAST_COMPLETED_URL = "lastCompletedUrl";
    private static final String KEY_NEXT_URL = "nextUrl";
    private static final String KEY_STATUS = "status";

    private final Path file;
    private final Properties properties = new Properties();

    public CrawlState(Path file) {
        this.file = file;
    }

    public void load() throws IOException {
        if (!Files.exists(file)) {
            return;
        }
        try (InputStream in = Files.newInputStream(file)) {
            properties.load(in);
        }
    }

    public void saveCompleted(String currentUrl, String nextUrl) throws IOException {
        properties.setProperty(KEY_LAST_COMPLETED_URL, nullToEmpty(currentUrl));
        properties.setProperty(KEY_NEXT_URL, nullToEmpty(nextUrl));
        properties.setProperty(KEY_STATUS, nextUrl == null || nextUrl.isBlank() ? "DONE" : "RUNNING");
        persist();
    }

    public void saveInterrupted(String currentUrl) throws IOException {
        properties.setProperty(KEY_NEXT_URL, nullToEmpty(currentUrl));
        properties.setProperty(KEY_STATUS, "INTERRUPTED");
        persist();
    }

    public String resolveStartUrl(String defaultUrl) {
        String nextUrl = properties.getProperty(KEY_NEXT_URL, "").trim();
        return nextUrl.isBlank() ? defaultUrl : nextUrl;
    }

    public String getLastCompletedUrl() {
        return properties.getProperty(KEY_LAST_COMPLETED_URL, "").trim();
    }

    private void persist() throws IOException {
        Files.createDirectories(file.getParent());
        try (OutputStream out = Files.newOutputStream(file)) {
            properties.store(out, "Crawler progress");
        }
    }

    private String nullToEmpty(String value) {
        return value == null ? "" : value;
    }
}
