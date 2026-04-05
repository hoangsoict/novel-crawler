package com.crawler.base;

import org.jsoup.nodes.Document;

public interface ChapterExtractor {
    Chapter extract(Document document, String currentUrl);
}
