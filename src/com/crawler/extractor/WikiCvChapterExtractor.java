package com.crawler.extractor;

import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import com.crawler.base.Chapter;
import com.crawler.base.ChapterExtractor;
import com.crawler.base.CrawlerUtils;

public class WikiCvChapterExtractor implements ChapterExtractor {

    @Override
    public Chapter extract(Document document, String currentUrl) {
        String title = extractTitle(document);
        String content = extractContent(document);
        String nextUrl = extractNextUrl(document, currentUrl);
        return new Chapter(currentUrl, title, content, nextUrl);
    }

    private String extractTitle(Document doc) {
        StringBuilder title = new StringBuilder();
        for (Element element : doc.select("p.book-title")) {
            title.append(element.text().trim()).append(System.lineSeparator());
        }
        return title.toString().trim();
    }

    private String extractContent(Document doc) {
        Element content = doc.getElementById("bookContentBody");
        if (content == null) {
            return "";
        }

        content.select("br").append("\\n");
        StringBuilder builder = new StringBuilder();

        for (Element p : content.select("p")) {
            String text = p.text().replace("\\n", "\n").trim();
            if (!text.isEmpty()) {
                builder.append(text).append(System.lineSeparator()).append(System.lineSeparator());
            }
        }

        if (builder.length() == 0) {
            return content.text().replace("\\n", "\n").trim();
        }

        return builder.toString().trim();
    }

    private String extractNextUrl(Document doc, String currentUrl) {
        Elements buttons = doc.select("a.btn-bot");
        for (Element button : buttons) {
            if (button.text() != null && button.text().contains("Chương sau")) {
                String href = button.attr("abs:href");
                if (href != null && !href.isBlank()) {
                    return href;
                }
                return CrawlerUtils.resolve(currentUrl, button.attr("href"));
            }
        }
        return null;
    }
}
