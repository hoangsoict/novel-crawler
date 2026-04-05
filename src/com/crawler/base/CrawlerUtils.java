package com.crawler.base;

import java.net.URI;

public final class CrawlerUtils {
    private CrawlerUtils() {
    }

    public static String resolve(String baseUrl, String href) {
        if (href == null || href.isBlank()) {
            return null;
        }
        try {
            return URI.create(baseUrl).resolve(href).toString();
        } catch (Exception e) {
            return href;
        }
    }

    public static String extractSlugFromUrl(String url) {
        try {
            String path = URI.create(url).getPath();
            String[] parts = path.split("/");
            return parts.length > 2 ? parts[2] : "output";
        } catch (Exception e) {
            return "output";
        }
    }
    
    public static void sleep(long time, String log) throws InterruptedException {
    	System.out.println("Sleep " + log + " : " +  time + " ms");
    	Thread.sleep(time);
    }
}
