package com.crawler;

import org.jsoup.Connection;
import org.jsoup.HttpStatusException;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ThreadLocalRandom;

public class WikiCvCrawler {

    private static final String START_URL =
            "https://wikicv.net/truyen/nay-that-khong-phai-may-moc-phi-thang/1-chuong-1-lan-dau-khong-che-aP6JesQsRDfw6u4u";

    private static final int MAX_RETRY = 5;
    private static final int TIMEOUT_MS = 20000;

    // Delay thường giữa các request
    private static final int MIN_DELAY_MS = 0;
    private static final int MAX_DELAY_MS = 2000;

    // Retry backoff
    private static final int RETRY_BASE_DELAY_MS = 2000;
    private static final int RETRY_MAX_JITTER_MS = 2500;

    // Nếu nghi anti-bot / Cloudflare thì nghỉ lâu hơn
    private static final int ANTI_BOT_MIN_DELAY_MS = 5000;
    private static final int ANTI_BOT_MAX_DELAY_MS = 10000;

    // Nghỉ dài sau mỗi N chương
    private static final int LONG_BREAK_EVERY_N_CHAPTERS = 50;
    private static final int LONG_BREAK_MIN_MS = 5000;
    private static final int LONG_BREAK_MAX_MS = 10000;

    private static final String FILE_NAME = extractSlugFromUrl(START_URL);
    private static final String DIR = "E:\\";
    private static final String OUTPUT_FILE = DIR + FILE_NAME + ".txt";
    private static final String RESUME_FILE = DIR + FILE_NAME + ".resume.txt";
    private static final String ERROR_LOG_FILE = DIR + FILE_NAME + ".error.log";
    private static final String CHECKPOINT_FILE = DIR + FILE_NAME + ".checkpoint.txt";
    private static final String WRITTEN_FILE = DIR + FILE_NAME + ".written.txt";

    private static final List<String> USER_AGENTS = List.of(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"
    );

    public static void main(String[] args) {
        try {
            crawlMetadata(resolveStartUrl(), OUTPUT_FILE);
            System.out.println("Hoàn tất. File output: " + OUTPUT_FILE);
        } catch (Exception e) {
            System.err.println("Crawler lỗi: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public static void crawlMetadata(String startUrl, String outputFile) throws IOException, InterruptedException {
        Set<String> visited = new HashSet<>();
        Map<String, String> checkpointMap = loadCheckpointMap();
        Set<String> writtenUrls = loadWrittenUrls();

        String currentUrl = resolveNextUnfinishedUrl(startUrl, checkpointMap, writtenUrls);
        int successCount = 0;

        if (!currentUrl.equals(startUrl)) {
            System.out.println("Resume nhanh từ URL chưa hoàn tất: " + currentUrl);
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(outputFile, true))) {
            while (currentUrl != null && !currentUrl.isBlank() && !visited.contains(currentUrl)) {
                visited.add(currentUrl);

                try {
                    Document doc = fetchWithRetry(currentUrl);

                    String bookTitle = extractBookTitle(doc);
                    String content = extractBookContent(doc);
                    String nextUrl = extractNextChapterUrl(doc, currentUrl);

                    // Chỉ ghi output nếu URL này chưa được ghi thành công
                    if (!writtenUrls.contains(currentUrl)) {
                        writer.write(bookTitle);
                        writer.newLine();
                        writer.write(content);
                        addSplitChapter(writer);
                        writer.flush();

                        appendWrittenUrl(currentUrl);
                        writtenUrls.add(currentUrl);

                        System.out.println("Đã ghi output: " + currentUrl);
                    } else {
                        System.out.println("Bỏ qua ghi output vì đã có rồi: " + currentUrl);
                    }

                    // Chỉ append checkpoint nếu currentUrl chưa từng có
                    if (!checkpointMap.containsKey(currentUrl)) {
                        appendCheckpoint(currentUrl, nextUrl);
                    }
                    checkpointMap.put(currentUrl, nextUrl == null ? "" : nextUrl);

                    // Lưu resume sang URL kế tiếp
                    saveResumeUrl(nextUrl);

                    currentUrl = nextUrl;
                    successCount++;

                    // Nghỉ ngẫu nhiên giữa các chương
                    randomSleep(MIN_DELAY_MS, MAX_DELAY_MS);

                    // Nghỉ dài sau mỗi N chương
                    if (successCount % LONG_BREAK_EVERY_N_CHAPTERS == 0) {
                        longBreak(successCount);
                    }

                } catch (Exception e) {
                    logError("Lỗi khi crawl URL: " + currentUrl + " | " + e.getMessage());
                    saveResumeUrl(currentUrl);
                    throw e;
                }
            }

            clearResumeFile();
        }
    }

    private static Document fetchWithRetry(String url) throws InterruptedException, IOException {
        Exception lastException = null;

        System.out.println("Đang fetch: " + url);

        // Delay trước request đầu tiên
        randomSleep(MIN_DELAY_MS, MAX_DELAY_MS);

        for (int attempt = 1; attempt <= MAX_RETRY; attempt++) {
            String userAgent = getRandomUserAgent();

            try {
                System.out.println("Attempt " + attempt + " | UA: " + userAgent);

                Connection.Response response = Jsoup.connect(url)
                        .userAgent(userAgent)
                        .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
                        .header("Accept-Language", "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7")
                        .header("Cache-Control", "no-cache")
                        .header("Pragma", "no-cache")
                        .referrer("https://wikicv.net/")
                        .timeout(TIMEOUT_MS)
                        .followRedirects(true)
                        .ignoreHttpErrors(true)
                        .method(Connection.Method.GET)
                        .execute();

                int statusCode = response.statusCode();
                String body = response.body();

                if (statusCode >= 200 && statusCode < 300) {
                    Document doc = response.parse();

                    if (doc.getElementById("bookContentBody") == null && looksSuspiciousEmptyPage(doc, body)) {
                        lastException = new IOException("Trang trả về bất thường, thiếu nội dung chính: " + url);
                        System.err.println(lastException.getMessage());

                        if (attempt < MAX_RETRY) {
                            randomSleep(ANTI_BOT_MIN_DELAY_MS, ANTI_BOT_MAX_DELAY_MS);
                            continue;
                        }
                        throw (IOException) lastException;
                    }

                    return doc;
                }

                if (statusCode == 403 || statusCode == 429 || statusCode == 503) {
                    lastException = new IOException("HTTP " + statusCode + " - nghi anti-bot/rate-limit tại URL: " + url);
                    System.err.println(lastException.getMessage());

                    if (attempt < MAX_RETRY) {
                        long sleep = getBackoffDelay(attempt);
                        System.out.println("Retry sau " + sleep + " ms");
                        Thread.sleep(sleep);
                        continue;
                    }
                    throw (IOException) lastException;
                }

                lastException = new HttpStatusException("HTTP error fetching URL", statusCode, url);
                System.err.println("HTTP " + statusCode + " với URL: " + url);

                if (attempt < MAX_RETRY) {
                    long sleep = getBackoffDelay(attempt);
                    System.out.println("Retry sau " + sleep + " ms");
                    Thread.sleep(sleep);
                }

            } catch (SocketTimeoutException e) {
                lastException = e;
                System.err.println("Timeout lần " + attempt + " với URL: " + url);

                if (attempt < MAX_RETRY) {
                    long sleep = getBackoffDelay(attempt);
                    System.out.println("Retry sau " + sleep + " ms");
                    Thread.sleep(sleep);
                }

            } catch (IOException e) {
                lastException = e;
                System.err.println("Lỗi IO lần " + attempt + " với URL: " + url + " - " + e.getMessage());

                if (attempt < MAX_RETRY) {
                    long sleep = getBackoffDelay(attempt);
                    System.out.println("Retry sau " + sleep + " ms");
                    Thread.sleep(sleep);
                }
            }
        }

        throw new IOException("Fetch thất bại sau " + MAX_RETRY + " lần: " + url, lastException);
    }

    private static String extractBookTitle(Document doc) {
        Elements titles = doc.select("p.book-title");
        StringBuilder title = new StringBuilder();

        for (Element element : titles) {
            title.append(element.text().trim()).append("\r\n");
        }

        return title.toString().trim();
    }

    private static String extractBookContent(Document doc) {
        Element content = doc.getElementById("bookContentBody");
        if (content == null) {
            return "";
        }

        // Giữ xuống dòng nếu có br
        content.select("br").append("\\n");

        StringBuilder sb = new StringBuilder();

        // Ưu tiên lấy từng p để giữ cấu trúc đoạn
        for (Element p : content.select("p")) {
            String text = p.text().replace("\\n", "\n").trim();
            if (!text.isEmpty()) {
                sb.append(text).append("\n\n");
            }
        }

        // Fallback nếu không có p
        if (sb.length() == 0) {
            String raw = content.text().replace("\\n", "\n").trim();
            if (!raw.isEmpty()) {
                sb.append(raw);
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

    private static void addSplitChapter(BufferedWriter writer) throws IOException {
        writer.write("\n\n--------------------------------\n\n");
    }

    private static void randomSleep(int minMs, int maxMs) throws InterruptedException {
        long sleep = ThreadLocalRandom.current().nextLong(minMs, maxMs + 1L);
        System.out.println("Sleep " + sleep + " ms");
        Thread.sleep(sleep);
    }

    private static void longBreak(int successCount) throws InterruptedException {
        long sleep = ThreadLocalRandom.current().nextLong(LONG_BREAK_MIN_MS, LONG_BREAK_MAX_MS + 1L);
        System.out.println("Đã crawl " + successCount + " chương. Nghỉ dài " + sleep + " ms...");
        Thread.sleep(sleep);
    }

    private static long getBackoffDelay(int attempt) {
        long exponential = (long) (RETRY_BASE_DELAY_MS * Math.pow(2, attempt - 1));
        long jitter = ThreadLocalRandom.current().nextLong(RETRY_MAX_JITTER_MS + 1L);
        return exponential + jitter;
    }

    private static String getRandomUserAgent() {
        int index = ThreadLocalRandom.current().nextInt(USER_AGENTS.size());
        return USER_AGENTS.get(index);
    }


    private static boolean looksSuspiciousEmptyPage(Document doc, String body) {
        if (doc == null) {
            return true;
        }

        String text = doc.text() == null ? "" : doc.text().trim().toLowerCase();
        String html = body == null ? "" : body.trim().toLowerCase();

        if (text.isEmpty() || html.isEmpty()) {
            return true;
        }

        return text.contains("access denied")
                || text.contains("forbidden")
                || text.contains("temporarily unavailable")
                || text.contains("request blocked")
                || text.contains("too many requests")
                || html.contains("access denied")
                || html.contains("request blocked");
    }

    private static String resolveStartUrl() {
        try {
            File resume = new File(RESUME_FILE);
            if (resume.exists()) {
                String url = Files.readString(resume.toPath(), StandardCharsets.UTF_8).trim();
                if (!url.isBlank()) {
                    System.out.println("Resume từ URL lỗi gần nhất: " + url);
                    return url;
                }
            }
        } catch (Exception e) {
            System.err.println("Không đọc được file resume: " + e.getMessage());
        }
        return START_URL;
    }

    private static void saveResumeUrl(String url) {
        if (url == null || url.isBlank()) {
            return;
        }
        try {
            Files.writeString(new File(RESUME_FILE).toPath(), url, StandardCharsets.UTF_8);
        } catch (Exception e) {
            System.err.println("Không lưu được resume file: " + e.getMessage());
        }
    }

    private static void clearResumeFile() {
        try {
            File file = new File(RESUME_FILE);
            if (file.exists() && !file.delete()) {
                System.err.println("Không xóa được file resume.");
            }
        } catch (Exception e) {
            System.err.println("Lỗi khi xóa file resume: " + e.getMessage());
        }
    }

    private static void logError(String message) {
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(ERROR_LOG_FILE, true))) {
            bw.write(message);
            bw.newLine();
        } catch (Exception e) {
            System.err.println("Không ghi được error log: " + e.getMessage());
        }
    }

    private static Map<String, String> loadCheckpointMap() {
        Map<String, String> result = new HashMap<>();
        File file = new File(CHECKPOINT_FILE);

        if (!file.exists()) {
            return result;
        }

        try {
            List<String> lines = Files.readAllLines(file.toPath(), StandardCharsets.UTF_8);
            for (String line : lines) {
                if (line == null || line.isBlank()) {
                    continue;
                }

                String[] parts = line.split("\\|", 2);
                String currentUrl = parts.length > 0 ? parts[0].trim() : "";
                String nextUrl = parts.length > 1 ? parts[1].trim() : "";

                if (!currentUrl.isEmpty()) {
                    result.put(currentUrl, nextUrl);
                }
            }
            System.out.println("Đã load " + result.size() + " checkpoint.");
        } catch (Exception e) {
            System.err.println("Không đọc được checkpoint file: " + e.getMessage());
        }

        return result;
    }

    private static void appendCheckpoint(String currentUrl, String nextUrl) {
        if (currentUrl == null || currentUrl.isBlank()) {
            return;
        }

        String line = currentUrl + "|" + (nextUrl == null ? "" : nextUrl);

        try (BufferedWriter bw = new BufferedWriter(new FileWriter(CHECKPOINT_FILE, true))) {
            bw.write(line);
            bw.newLine();
        } catch (Exception e) {
            System.err.println("Không ghi được checkpoint file: " + e.getMessage());
        }
    }

    private static Set<String> loadWrittenUrls() {
        Set<String> result = new HashSet<>();
        File file = new File(WRITTEN_FILE);

        if (!file.exists()) {
            return result;
        }

        try {
            List<String> lines = Files.readAllLines(file.toPath(), StandardCharsets.UTF_8);
            for (String line : lines) {
                String url = line == null ? "" : line.trim();
                if (!url.isEmpty()) {
                    result.add(url);
                }
            }
            System.out.println("Đã load " + result.size() + " URL đã ghi output.");
        } catch (Exception e) {
            System.err.println("Không đọc được written file: " + e.getMessage());
        }

        return result;
    }

    private static void appendWrittenUrl(String url) {
        if (url == null || url.isBlank()) {
            return;
        }

        try (BufferedWriter bw = new BufferedWriter(new FileWriter(WRITTEN_FILE, true))) {
            bw.write(url);
            bw.newLine();
        } catch (Exception e) {
            System.err.println("Không ghi được written file: " + e.getMessage());
        }
    }

    private static String resolveNextUnfinishedUrl(String startUrl,
                                                   Map<String, String> checkpointMap,
                                                   Set<String> writtenUrls) {
        String current = startUrl;
        Set<String> guard = new HashSet<>();

        while (current != null
                && !current.isBlank()
                && checkpointMap.containsKey(current)
                && writtenUrls.contains(current)
                && !guard.contains(current)) {

            guard.add(current);
            String next = checkpointMap.get(current);

            if (next == null || next.isBlank()) {
                return current;
            }

            current = next;
        }

        return (current == null || current.isBlank()) ? startUrl : current;
    }

    private static String extractSlugFromUrl(String url) {
        try {
            String path = java.net.URI.create(url).getPath();
            String[] parts = path.split("/");
            return parts.length > 2 ? parts[2] : "output";
        } catch (Exception e) {
            return "output";
        }
    }
}