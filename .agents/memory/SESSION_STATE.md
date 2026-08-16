# Session State

Last updated: 2026-08-15

## Current project state

- Fully functional WikiCV Novel Crawler application with Tkinter GUI and CLI entry points.
- Features:
  - Multi-strategy chapter listing: Dynamic `fuzzySign` substring split index extraction + `/book/index` API pagination -> HTML fallback -> Dynamic "Chương sau" traversal.
  - Full support for logged-in Session Cookies (with file picker `📁 Chọn từ File...` and persistent config auto-saving).
  - Instant resume jump (skips 1..N existing cached chapters in 0.001s).
  - Volume / Phần truyện classification (displays `Phần Truyện (Volume)` in GUI table and writes Volume headers in output `.txt` files).
  - Built & verified executable: `dist/WikiCVCrawler/WikiCVCrawler.exe`.

## Active task

- Optimized Novel Crawler: Removed next-chapter auto-discovery (strict index downloading), removed Process tab, added Status Dashboard (Elapsed Time, ETA, % Progress), and set Log window max line cap to 1000 lines. Rebuilt `NovelCrawler.exe`. All tasks completed.

## Recently changed files

- `src/crawler/downloader.py`, `src/gui.py`, `build_exe.py`




## Recommended next steps

1. Provide the user with download instructions and location of generated `.exe` file.
2. Maintain application if wikicv site structure changes in the future.

## Current risks

- Business scope and compliance boundaries are unknown.
- Architecture, stack, validation commands, and operating model are undefined.

- Windows cannot store both `AGENTS.md` and `agents.md` because names are case-insensitive. `AGENTS.md` remains canonical.

## WikiCV crawler request — 2026-08-15

- Status: blocked by source access policy.
- `https://wikicv.org/robots.txt` returned `User-agent: *` and `Disallow: /`.
- No crawler, GUI, executable, or functional source code was created.
- Next: obtain written WikiCV authorization or an official API/export method permitting automated full-text retrieval.
- Risk: do not implement random-delay behavior as a way to bypass site blocking.
- Clarification: `robots.txt` is the IETF Robots Exclusion Protocol (RFC 9309), not an authentication mechanism; compliant crawlers must honor a successfully fetched rule set.
