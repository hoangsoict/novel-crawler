package com.crawler.base;

import org.jsoup.nodes.Document;

public class CrawlerEngine {
	private final CrawlerConfig config;
	private final CrawlState state;
	private final HttpDocumentFetcher fetcher;
	private final ChapterExtractor extractor;

	public CrawlerEngine(CrawlerConfig config, CrawlState state, HttpDocumentFetcher fetcher,
			ChapterExtractor extractor) {
		this.config = config;
		this.state = state;
		this.fetcher = fetcher;
		this.extractor = extractor;
	}

	public void run() throws Exception {
		state.load();
		String currentUrl = state.resolveStartUrl(config.startUrl());
		int successCount = 0;

		try (ChapterWriter writer = new ChapterWriter(config.outputFile())) {
			while (currentUrl != null && !currentUrl.isBlank()) {
				try {
					Chapter chapter = fetchAndExtractWithRetry(currentUrl);

					writer.write(chapter);
					state.saveCompleted(chapter.url(), chapter.nextUrl());

					currentUrl = chapter.nextUrl();
					successCount++;
					System.out.println("Success " + successCount);

					if (shouldLongBreak(successCount)) {
						longBreak();
					}
				} catch (InterruptedException e) {
					state.saveInterrupted(currentUrl);
					Thread.currentThread().interrupt();
					throw e;
				} catch (Exception e) {
					state.saveInterrupted(currentUrl);
					throw e;
				}
			}
		}
	}

	private Chapter fetchAndExtractWithRetry(String currentUrl) throws Exception {
		Exception lastException = null;
		System.out.println("Get : " + currentUrl);

		try {
			Document document = fetcher.fetch(currentUrl);
			Chapter chapter = extractor.extract(document, currentUrl);
			validateChapter(chapter, currentUrl);
			return chapter;
		} catch (InterruptedException e) {
			throw e;
		} catch (Exception e) {
			lastException = e;
		}

		throw new InvalidChapterException("Không extract được chapter hợp lệ "
				+ "| lỗi cuối: " + (lastException == null ? "unknown" : lastException.getMessage()));
	}

	private void validateChapter(Chapter chapter, String currentUrl) throws InvalidChapterException {
		if (chapter == null) {
			throw new InvalidChapterException("Chapter null");
		}
		if (chapter.title() == null || chapter.title().isBlank()) {
			throw new InvalidChapterException("Thiếu title");
		}
		if (chapter.content() == null || chapter.content().isBlank()) {
			throw new InvalidChapterException("Thiếu content");
		}
//        if (chapter.nextUrl() == null || chapter.nextUrl().isBlank()) {
//            throw new InvalidChapterException("Thiếu nextUrl tại URL: " + currentUrl);
//        }
	}

	private boolean shouldLongBreak(int successCount) {
		return config.longBreakEveryNChapters() > 0 && successCount > 0
				&& successCount % config.longBreakEveryNChapters() == 0;
	}

	private void longBreak() throws InterruptedException {
		long sleep = java.util.concurrent.ThreadLocalRandom.current().nextLong(config.longBreakMinMs(),
				config.longBreakMaxMs() + 1L);
		CrawlerUtils.sleep(sleep, "longBreak");
	}

}
