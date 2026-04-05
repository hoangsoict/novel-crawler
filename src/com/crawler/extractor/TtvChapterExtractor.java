package com.crawler.extractor;

import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import com.crawler.base.Chapter;
import com.crawler.base.ChapterExtractor;

public class TtvChapterExtractor implements ChapterExtractor {

    @Override
    public Chapter extract(Document document, String currentUrl) {
        String title = extractTitle(document);
        String content = extractContent(document);
        String nextUrl = extractNextUrl(document, currentUrl);
        return new Chapter(currentUrl, title, content, nextUrl);
    }

    private String extractTitle(Document doc) {
        Element h2 = doc.selectFirst("div.chapter h2");
        String title = h2 != null ? h2.text() : "";
        return title.toString().trim();
    }

    private String extractContent(Document doc) {
    	
    	Element content = doc.selectFirst("div.box-chap");

        if (content == null) {
            return "";
        }

        return content.text().replace(". ", ".\n").trim();
      
    }

    private String extractNextUrl(Document doc, String currentUrl) {
    	java.util.regex.Pattern pattern = java.util.regex.Pattern.compile("chuong-(\\d+)");
        java.util.regex.Matcher matcher = pattern.matcher(currentUrl);

        if (matcher.find()) {
            int current = Integer.parseInt(matcher.group(1));
            int next = current + 1;
            return matcher.replaceFirst("chuong-" + next);
        }

        return null; // fallback
    }
}
