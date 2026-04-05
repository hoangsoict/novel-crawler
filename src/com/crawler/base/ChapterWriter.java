package com.crawler.base;

import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class ChapterWriter implements Closeable {
    private final BufferedWriter writer;

    public ChapterWriter(Path file) throws IOException {
        Files.createDirectories(file.getParent());
        this.writer = Files.newBufferedWriter(
                file,
                StandardOpenOption.CREATE,
                StandardOpenOption.APPEND
        );
    }

    public void write(Chapter chapter) throws IOException {
        writer.write(chapter.title());
        writer.newLine();
        writer.write(chapter.content());
        writer.newLine();
        writer.newLine();
        writer.write("--------------------------------");
        writer.newLine();
        writer.newLine();
        writer.flush();
    }

    @Override
    public void close() throws IOException {
        writer.close();
    }
}
