# Session State

Last updated: 2026-08-16

## Current project state

- Fully functional Novel Crawler application v1.1.0 with Tkinter GUI and CLI entry points.
- Branding: Novel Crawler (`assets/icon.ico`, `NovelCrawler.exe`).
- Features:
  - Multi-source support (`wikicv.org` & `metruyenchuvn.org`).
  - Auto Cloudflare WARP Reset on error (`warp-cli disconnect` -> `warp-cli connect`).
  - Session-based ETA calculation & Status Dashboard.
  - Automatic input locking during download & live dynamic parameter updates.
  - Automatic single last-chapter integrity verification (JSON cache & `.txt` content snippet).
  - Auto-moving 100% completed text files to `downloads/Finish/`.
  - Automated Pre-flight validation in `build_exe.py` preventing Tkinter float font size regressions.
  - Codebase hosted on GitHub: `https://github.com/hoangsoict/novel-crawler`.

## Active task

- Pushed full codebase to GitHub repository `https://github.com/hoangsoict/novel-crawler`. All tasks completed.

## Recently changed files

- `src/crawler/parser.py`, `src/crawler/storage.py`, `src/crawler/downloader.py`, `src/gui.py`, `build_exe.py`, `.gitignore`

## Recommended next steps

1. Share GitHub repository link with the user: `https://github.com/hoangsoict/novel-crawler`.
2. Maintain application and adapters if source site structures change in the future.
