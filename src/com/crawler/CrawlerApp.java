package com.crawler;

import java.nio.file.Path;

import com.crawler.base.ChapterExtractor;
import com.crawler.base.CrawlState;
import com.crawler.base.CrawlerConfig;
import com.crawler.base.CrawlerEngine;
import com.crawler.base.HttpDocumentFetcher;
import com.crawler.extractor.TtvChapterExtractor;
import com.crawler.extractor.WikiCvChapterExtractor;

public class CrawlerApp {
    public static void main(String[] args) throws Exception {
        Path baseDir = Path.of("E:/");
        String startUrl =  null;
        CrawlerConfig config = null ;
        CrawlState state = null ;
        ChapterExtractor extractor = null;

//        startUrl = "https://wikicv.net/truyen/nay-that-khong-phai-may-moc-phi-thang/1-chuong-1-lan-dau-khong-che-aP6JesQsRDfw6u4u";
        startUrl = "https://tangthuvien.top/doc-truyen/cau-tai-vu-su-the-gioi-tu-dia-tien/chuong-1";

        
        if (startUrl.contains("wikicv.net")) {
        	config = CrawlerConfig.defaultWikiCv(baseDir, "nay-that-khong-phai-may-moc-phi-thang",startUrl);
            state = new CrawlState(config.progressFile());
            extractor = new WikiCvChapterExtractor();
        } 
        else if(startUrl.contains("tangthuvien")) {
        	config = CrawlerConfig.defaultTtvCv(baseDir, "cau-tai-vu-su-the-gioi-tu-dia-tien",startUrl);
	        state = new CrawlState(config.progressFile());
	        extractor = new TtvChapterExtractor();
        }
        
        HttpDocumentFetcher fetcher = new HttpDocumentFetcher(config);
        new CrawlerEngine(config, state, fetcher, extractor).run();
    }
}
