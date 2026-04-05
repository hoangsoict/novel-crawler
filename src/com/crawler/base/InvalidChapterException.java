package com.crawler.base;

import java.io.IOException;

public class InvalidChapterException extends IOException {
    public InvalidChapterException(String message) {
        super(message);
    }
}
