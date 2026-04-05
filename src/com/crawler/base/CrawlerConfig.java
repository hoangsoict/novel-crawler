package com.crawler.base;

import java.nio.file.Path;
import java.util.List;

public record CrawlerConfig(
        String siteName,
        String startUrl,
        Path outputFile,
        Path progressFile,
        int maxRetry,
        int timeoutMs,
        int minDelayMs,
        int maxDelayMs,
        int minRetryDelay,
        int maxRetryDelay,
        int longBreakEveryNChapters,
        int longBreakMinMs,
        int longBreakMaxMs,
        List<String> userAgents
) {
    public static CrawlerConfig defaultWikiCv(Path baseDir, String startUrl) {
        String slug = CrawlerUtils.extractSlugFromUrl(startUrl);
        return new CrawlerConfig(
                "wikicv",
                startUrl,
                baseDir.resolve(slug + ".txt"),
                baseDir.resolve(slug + ".progress.txt"),
                5,
                30_000,
                0,
                2_000,
                5_000,
                10_000,
                50,
                5_000,
                10_000,
                List.of(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"
                )
        );
    }
}
