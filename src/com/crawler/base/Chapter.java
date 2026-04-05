package com.crawler.base;

public record Chapter(String url, String title, String content, String nextUrl) {

    public boolean isValid() {
        return notBlank(title) && notBlank(content) && notBlank(nextUrl);
    }

    private boolean notBlank(String value) {
        return value != null && !value.isBlank();
    }
}
