package com.crawler.base;

import org.jsoup.Connection;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;

import java.io.IOException;
import java.net.SocketTimeoutException;
import java.util.concurrent.ThreadLocalRandom;

public class HttpDocumentFetcher {
    private final CrawlerConfig config;

    public HttpDocumentFetcher(CrawlerConfig config) {
        this.config = config;
    }

    public Document fetch(String url) throws IOException, InterruptedException {
        Exception lastException = null;

        for (int attempt = 1; attempt <= config.maxRetry(); attempt++) {
            try {
                randomSleep(config.minDelayMs(), config.maxDelayMs());
                Connection.Response response = Jsoup.connect(url)
                        .userAgent(randomUserAgent())
                        .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
                        .header("Accept-Language", "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7")
                        .header("Cache-Control", "no-cache")
                        .header("Pragma", "no-cache")
                        .referrer("https://wikicv.net/")
                        .timeout(config.timeoutMs())
                        .followRedirects(true)
                        .ignoreHttpErrors(true)
                        .method(Connection.Method.GET)
                        .execute();

                return response.parse();
            } catch (SocketTimeoutException e) {
                lastException = e;
            } catch (IOException e) {
                lastException = e;
            }
            
            if(lastException != null) {
            	System.err.println("Error : " + attempt + " - " + lastException.getMessage());
            }

            if (attempt < config.maxRetry()) {
            	CrawlerUtils.sleep(backoffDelay(attempt),"retryFetchUrl");
            }
        }

        throw new IOException("Không fetch được URL sau " + config.maxRetry() + " lần: ", lastException);
    }

    private String randomUserAgent() {
        int index = ThreadLocalRandom.current().nextInt(config.userAgents().size());
        return config.userAgents().get(index);
    }

    private void randomSleep(int minMs, int maxMs) throws InterruptedException {
    	CrawlerUtils.sleep(ThreadLocalRandom.current().nextLong(minMs, maxMs + 1L),"random");
    }

    private long backoffDelay(int attempt) {
        long exponential = (long) (config.minRetryDelay() * Math.pow(2, attempt - 1));
        long jitter = ThreadLocalRandom.current().nextLong(config.maxRetryDelay() + 1L);
        return exponential + jitter;
    }
    
}
