package com.crawler;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.net.SocketTimeoutException;
import java.util.HashSet;
import java.util.Set;

public class WikiCvCrawler {

	private static final String START_URL = "https://wikicv.net/truyen/hai-tac-chi-thien-phu-he-thong/chuong-1-san-giet-WtY8a8QsRBD9MutQ";

	private static final int MAX_RETRY = 5;
	private static final int RETRY_DELAY_MS = 2000;
	private static final int DELAY_MS = 1000;
	private static final int TIMEOUT_MS = 20000;
	private static final String FILE_NAME = START_URL.split("/")[4];
	private static final String DIR = "E:\\";


	public static void main(String[] args) {
		try {
			crawlMetadata(START_URL, DIR+FILE_NAME+".txt");
			System.out.println("Hoàn tất. File output: " + DIR+FILE_NAME+".txt");
		} catch (Exception e) {
			System.err.println("Crawler lỗi: " + e.getMessage());
			e.printStackTrace();
		}
	}

	public static void crawlMetadata(String startUrl, String outputFile) throws IOException, InterruptedException {
		Set<String> visited = new HashSet<>();
		String currentUrl = startUrl;

		try (BufferedWriter writer = new BufferedWriter(new FileWriter(outputFile, true))) {
			while (currentUrl != null && !currentUrl.isBlank() && !visited.contains(currentUrl)) {
				visited.add(currentUrl);

				Document doc = fetchWithRetry(currentUrl);
//                System.out.println(doc.text());

				String bookTitle = extractBookTitle(doc);
				String content = extractBookContent(doc);
				String nextUrl = extractNextChapterUrl(doc, currentUrl);

				writer.write(bookTitle);
				writer.newLine();
				writer.write(content);
				addSplitChapter(writer);
				writer.flush();

				currentUrl = nextUrl;
			}
		}
	}
	
	private static void addSplitChapter(BufferedWriter writer) throws IOException {
		writer.write("\n\n--------------------------------\n\n");
	}

	private static Document fetchWithRetry(String url) throws InterruptedException, IOException {
		Exception lastException = null;
		System.out.println(url);
		Thread.sleep(DELAY_MS);
		for (int attempt = 1; attempt <= MAX_RETRY; attempt++) {
			try {
				return Jsoup.connect(url).userAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
						+ "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36").timeout(TIMEOUT_MS).get();
			} catch (SocketTimeoutException e) {
				lastException = e;
				System.err.println("Timeout lần " + attempt + " với URL: " + url);
			} catch (IOException e) {
				lastException = e;
				System.err.println("Lỗi IO lần " + attempt + " với URL: " + url + " - " + e.getMessage());
			}

			if (attempt < MAX_RETRY) {
				Thread.sleep(RETRY_DELAY_MS);
			}
		}

		throw new IOException("Fetch thất bại sau " + MAX_RETRY + " lần: " + url, lastException);
	}

	private static String extractBookTitle(Document doc) {
		Elements titles = doc.select("p.book-title");
		String title = "";
		for (Element element : titles) {
			title += element.text().trim() + "\r\n";
		}

		return title;
	}

	private static String extractBookContent(Document doc) {
		Element content = doc.getElementById("bookContentBody");
		if (content == null)
			return "";

		// xử lý <br>
		content.select("br").append("\\n");

		StringBuilder sb = new StringBuilder();

		for (Element p : content.select("p")) {
			String text = p.text().replace("\\n", "\n").trim();

			if (!text.isEmpty()) {
				sb.append(text).append("\n\n");
			}
		}

		return sb.toString().trim();
	}

	private static String extractNextChapterUrl(Document doc, String currentUrl) {
		Elements buttons = doc.select("a.btn-bot");

		for (Element btn : buttons) {
			String text = btn.text();
			if (text != null && text.contains("Chương sau")) {
				String href = btn.attr("abs:href");
				if (href != null && !href.isBlank()) {
					return href;
				}

				// fallback nếu abs:href không ra
				String rawHref = btn.attr("href");
				if (rawHref != null && !rawHref.isBlank()) {
					if (rawHref.startsWith("http://") || rawHref.startsWith("https://")) {
						return rawHref;
					}
					return buildAbsoluteUrl(currentUrl, rawHref);
				}
			}
		}
		return null;
	}

	private static String buildAbsoluteUrl(String currentUrl, String href) {
		try {
			java.net.URI base = java.net.URI.create(currentUrl);
			return base.resolve(href).toString();
		} catch (Exception e) {
			return href;
		}
	}

	private static String safe(String value) {
		return value == null ? "" : value;
	}
}