import re
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from bs4 import BeautifulSoup
import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def dynamic_fuzzy_sign(text: str, idx: int = 35) -> str:
    """Perform WikiCV dynamic fuzzySign transformation on key string."""
    if len(text) <= idx:
        return text
    return text[idx:] + text[:idx]

def generate_signature(sign_key: str, start: int, size: int, split_idx: int = 35) -> str:
    """Generate SHA-256 signature required for /book/index API."""
    raw_text = f"{sign_key}{start}{size}"
    fuzzy_text = dynamic_fuzzy_sign(raw_text, split_idx)
    return hashlib.sha256(fuzzy_text.encode('utf-8')).hexdigest()

def fetch_novel_info(session: requests.Session, novel_url: str) -> Dict[str, Any]:
    """
    Fetch novel main page and extract metadata (book_id, sign_key, split_idx, title, synopsis).
    Supports multiple sources: wikicv.org, metruyenchuvn.org.
    """
    clean_url = novel_url.split('#')[0].rstrip('/')
    resp = session.get(clean_url, headers=DEFAULT_HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text

    if "metruyenchuvn.org" in clean_url:
        soup = BeautifulSoup(html, "html.parser")
        rid_match = re.search(r'var\s+rid\s*=\s*["\'](\d+)["\']', html)
        rid = rid_match.group(1) if rid_match else ""

        slug = clean_url.rstrip('/').split('/')[-1]
        book_id = rid if rid else slug

        title = ""
        cover_h1 = soup.select_one(".cover-info h1") or soup.select_one("h1") or soup.select_one("h2")
        if cover_h1:
            title = cover_h1.text.strip()
        if not title and soup.title:
            title = soup.title.text.split("-")[0].strip()
        if not title:
            title = "Truyện MeTruyenChuVN"

        synopsis_parts = []
        desc_div = soup.select_one("#gioithieu") or soup.select_one(".book-desc-detail") or soup.select_one(".book-desc")
        if desc_div:
            for el in desc_div.select("script, style, ins, .ads, .ad"):
                el.decompose()
            txt = desc_div.text.strip()
            if txt:
                synopsis_parts.append(txt)
        synopsis = "\n".join(synopsis_parts)

        return {
            "book_id": book_id,
            "sign_key": rid,
            "split_idx": 35,
            "title": title,
            "synopsis": synopsis,
            "url": clean_url,
            "source": "metruyenchuvn"
        }

    # Default WikiCV Source Parser
    if "Đã hết lượt truy cập" in html:
        raise ValueError(
            "Wikicv.org thông báo: Đã hết lượt truy cập đọc miễn phí (Guest Limit).\n"
            "💡 HƯỚNG DẪN KHẮC PHỤC:\n"
            "1. Đăng nhập tài khoản trên website wikicv.org bằng trình duyệt Web.\n"
            "2. Nhấn F12 (hoặc F12 -> Application / Storage -> Cookies) hoặc dùng tiện ích lấy Cookie.\n"
            "3. Dán Cookie vào ô 'Cookies (Tùy chọn)' trên ứng dụng rồi bấm 'Start download' để tiếp tục tải!"
        )

    soup = BeautifulSoup(html, "html.parser")

    # Extract bookId
    book_id_match = re.search(r'var\s+bookId\s*=\s*["\']([a-f0-9]+)["\']', html)
    book_id = book_id_match.group(1) if book_id_match else "unknown_book"

    # Extract signKey
    sign_key_match = re.search(r'var\s+signKey\s*=\s*["\']([a-f0-9]+)["\']', html)
    sign_key = sign_key_match.group(1) if sign_key_match else ""

    # Extract fuzzySign split index dynamically (e.g. text.substring(53) or text.substring(35))
    split_match = re.search(r'fuzzySign\(text\)\s*\{\s*return\s+text\.substring\((\d+)\)', html)
    split_idx = int(split_match.group(1)) if split_match else 35

    # Extract Title
    title = ""
    cover_h2 = soup.select_one(".cover-info h2") or soup.select_one("h2") or soup.select_one("h1")
    if cover_h2:
        title = cover_h2.text.strip()
    if not title and soup.title:
        title = soup.title.text.split("-")[0].strip()
    if not title:
        title = "Truyện WikiCV"

    # Extract Synopsis (Giới thiệu)
    synopsis_parts = []

    # 1. Look for Hán Việt / Tác giả in cover-info
    cover_info = soup.select_one(".cover-info") or soup.select_one(".book-info")
    if cover_info:
        for p in cover_info.find_all(["p", "div"]):
            txt = p.text.strip()
            if any(k in txt for k in ["Hán Việt:", "Tác giả:", "Tình trạng:", "Mới nhất:"]) and txt not in synopsis_parts:
                synopsis_parts.append(txt)

    # 2. Main description paragraphs in book-desc-detail
    desc_detail = soup.select_one(".book-desc-detail") or soup.select_one(".book-desc")
    if desc_detail:
        for el in desc_detail.select(".readmore, script, style"):
            el.decompose()
        for p in desc_detail.find_all(["p", "div"]):
            txt = p.text.strip()
            if txt and txt not in synopsis_parts:
                synopsis_parts.append(txt)
        if not synopsis_parts and desc_detail.text.strip():
            synopsis_parts.append(desc_detail.text.strip())

    synopsis = "\n".join(synopsis_parts)

    return {
        "book_id": book_id,
        "sign_key": sign_key,
        "split_idx": split_idx,
        "title": title,
        "synopsis": synopsis,
        "url": clean_url,
        "source": "wikicv"
    }

def fetch_chapter_list(session: requests.Session, book_id: str, sign_key: str, novel_url: str, split_idx: int = 35) -> List[Dict[str, str]]:
    """
    Fetch all chapters across pages with source specific strategies.
    Supports wikicv.org and metruyenchuvn.org.
    """
    all_chapters = []
    clean_url = novel_url.split('#')[0].rstrip('/')

    # Source Strategy 1: MeTruyenChuVN
    if "metruyenchuvn.org" in novel_url:
        rid = sign_key if sign_key and sign_key.isdigit() else ""
        if not rid:
            try:
                r = session.get(clean_url, headers=DEFAULT_HEADERS, timeout=15)
                rid_match = re.search(r'var\s+rid\s*=\s*["\'](\d+)["\']', r.text)
                if rid_match:
                    rid = rid_match.group(1)
            except Exception:
                pass

        seen_urls = set()
        if rid:
            page = 1
            while True:
                api_url = f"https://metruyenchuvn.org/get/listchap/{rid}?page={page}"
                try:
                    resp = session.get(api_url, headers=DEFAULT_HEADERS, timeout=15)
                    if resp.status_code != 200:
                        break
                    data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {"data": resp.text}
                    html_str = data.get("data", "") if isinstance(data, dict) else ""
                    if not html_str:
                        break

                    list_soup = BeautifulSoup(html_str, "html.parser")
                    added = 0
                    for a in list_soup.find_all('a', href=True):
                        href = a.get('href', '')
                        if href and not href.startswith('javascript:') and href != '#' and '/chuong-' in href:
                            full_url = f"https://metruyenchuvn.org{href}" if not href.startswith('http') else href
                            if full_url not in seen_urls:
                                seen_urls.add(full_url)
                                title = a.text.strip()
                                all_chapters.append({"title": title, "url": full_url, "volume": ""})
                                added += 1

                    if added == 0:
                        break
                    page += 1
                except Exception:
                    break

        if not all_chapters:
            try:
                resp = session.get(clean_url, headers=DEFAULT_HEADERS, timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        if href and not href.startswith('javascript:') and href != '#' and '/chuong-' in href:
                            full_url = f"https://metruyenchuvn.org{href}" if not href.startswith('http') else href
                            if full_url not in seen_urls:
                                seen_urls.add(full_url)
                                title = a.text.strip()
                                all_chapters.append({"title": title, "url": full_url, "volume": ""})
            except Exception:
                pass

        return all_chapters

    # Source Strategy 2: WikiCV API
    if book_id != "unknown_book" and sign_key:
        api_url = "https://wikicv.org/book/index"
        start = 0
        size = 501

        headers = dict(DEFAULT_HEADERS)
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers["Referer"] = clean_url

        try:
            current_volume = ""
            while True:
                sign = generate_signature(sign_key, start, size, split_idx)
                params = {
                    "bookId": book_id,
                    "start": start,
                    "size": size,
                    "signKey": sign_key,
                    "sign": sign
                }

                resp = session.get(api_url, params=params, headers=headers, timeout=15)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                chap_elements = soup.find_all(["h5", "li"])

                if not chap_elements:
                    break

                added_count = 0
                for el in chap_elements:
                    if el.name == "h5" and "volume-name" in el.get("class", []):
                        vol_txt = el.text.strip()
                        if vol_txt:
                            current_volume = vol_txt
                    elif el.name == "li" and "chapter-name" in el.get("class", []):
                        a = el.find("a", href=True)
                        if a:
                            href = a.get('href', '')
                            if href and href not in ["#", "#!", "javascript:void(0);", "/chuong-moi", "/chuong-moi/"] and not href.startswith("/redirect"):
                                clean_h = href.split('#')[0].rstrip('/')
                                if clean_h != clean_url:
                                    full_url = f"https://wikicv.org{href}" if not href.startswith('http') else href
                                    title = a.text.strip()
                                    if full_url not in [c["url"] for c in all_chapters]:
                                        all_chapters.append({
                                            "title": title,
                                            "url": full_url,
                                            "volume": current_volume
                                        })
                                        added_count += 1

                if added_count == 0:
                    break

                start += size
        except Exception:
            pass

    # Source Strategy 3: WikiCV HTML Scraping Fallback
    if not all_chapters:
        try:
            resp = session.get(clean_url, headers=DEFAULT_HEADERS, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                seen = set()
                raw_list = []
                for a in soup.find_all("a", href=lambda h: h and "/chuong-" in h):
                    href = a.get("href", "")
                    if not href or href in ["/chuong-moi", "/chuong-moi/"]:
                        continue
                    full_url = f"https://wikicv.org{href}" if not href.startswith("http") else href
                    if full_url in seen:
                        continue
                    seen.add(full_url)

                    title = a.text.strip()
                    num_match = re.search(r'chuong-(\d+)', href)
                    num = int(num_match.group(1)) if num_match else 999999

                    if not title or title.lower() in ["đọc", "đọc từ đầu", "mới nhất"]:
                        title = f"Chương {num}" if num != 999999 else "Chương 1"

                    if title.lower() in ["chương sau", "chương trước"]:
                        continue

                    raw_list.append({"title": title, "url": full_url, "num": num})

                raw_list.sort(key=lambda item: item["num"])
                
                chap1_items = [item for item in raw_list if item["num"] == 1]
                if chap1_items:
                    all_chapters.append({"title": chap1_items[0]["title"], "url": chap1_items[0]["url"], "volume": ""})
                else:
                    for item in raw_list:
                        all_chapters.append({"title": item["title"], "url": item["url"], "volume": ""})
        except Exception:
            pass

    return all_chapters

def fetch_chapter_content(session: requests.Session, chapter_url: str) -> Dict[str, Any]:
    """
    Fetch a single chapter page and extract body content and real chapter title.
    Supports wikicv.org and metruyenchuvn.org.
    """
    # MeTruyenChuVN chapter content parser
    if "metruyenchuvn.org" in chapter_url:
        resp = session.get(chapter_url, headers=DEFAULT_HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        real_title = ""
        h2 = soup.find("h2") or soup.find("h1")
        if h2:
            real_title = h2.text.strip()
        if not real_title and soup.title:
            real_title = soup.title.text.split("-")[-1].strip()

        content_div = soup.select_one(".truyen") or soup.select_one("#content") or soup.select_one(".content") or soup.select_one(".book-content")
        content = ""
        if content_div:
            for el in content_div.select("script, style, ins, .ads, .ad"):
                el.decompose()
            paragraphs = [p.text.strip() for p in content_div.find_all("p") if p.text.strip()]
            if paragraphs:
                content = "\n\n".join(paragraphs)
            else:
                content = content_div.text.strip()

        return {
            "title": real_title,
            "content": content,
            "next_url": ""
        }

    # WikiCV chapter content parser
    try:
        resp = session.get(chapter_url, headers=DEFAULT_HEADERS, timeout=15)
        if resp.status_code in [403, 429]:
            raise ValueError(
                "HẾT LƯỢT TRUY CẬP ĐỌC THỬ (HTTP 403/429 FORBIDDEN).\n"
                "Website wikicv.org giới hạn đọc vãng lai và yêu cầu Cookie tài khoản để đọc tiếp!\n"
                "👉 Vui lòng dán Cookie tài khoản (hoặc bấm '📁 Chọn từ File...') vào ô 'Cookies (Tùy chọn)' trên giao diện rồi bấm 'Start download' để tiếp tục tải!"
            )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in [403, 429]:
            raise ValueError(
                "HẾT LƯỢT TRUY CẬP ĐỌC THỬ (HTTP 403/429 FORBIDDEN).\n"
                "Website wikicv.org giới hạn đọc vãng lai và yêu cầu Cookie tài khoản để đọc tiếp!\n"
                "👉 Vui lòng dán Cookie tài khoản (hoặc bấm '📁 Chọn từ File...') vào ô 'Cookies (Tùy chọn)' trên giao diện rồi bấm 'Start download' để tiếp tục tải!"
            )
        raise e

    html = resp.text

    if "Đã hết lượt truy cập" in html:
        raise ValueError(
            "Wikicv.org thông báo: Đã hết lượt truy cập đọc miễn phí (Guest Limit).\n"
            "💡 HƯỚNG DẪN KHẮC PHỤC:\n"
            "1. Đăng nhập tài khoản trên website wikicv.org bằng trình duyệt Web.\n"
            "2. Nhấn F12 (hoặc F12 -> Application / Storage -> Cookies) hoặc dùng tiện ích lấy Cookie.\n"
            "3. Dán Cookie vào ô 'Cookies (Tùy chọn)' trên ứng dụng rồi bấm 'Start download' để tiếp tục tải!"
        )

    soup = BeautifulSoup(html, "html.parser")

    real_title = ""
    if soup.title and soup.title.text.strip():
        doc_title = soup.title.text.strip()
        if "-" in doc_title:
            real_title = doc_title.split("-")[-1].strip()
        else:
            real_title = doc_title
    
    if not real_title:
        h1 = soup.find("h1") or soup.find("h2")
        if h1:
            real_title = h1.text.strip()

    content_div = soup.select_one(".book-content") or soup.select_one("#bookContent") or soup.select_one(".content")
    content = ""
    if content_div:
        for el in content_div.select("script, style, ins, .ads, .ad"):
            el.decompose()
        paragraphs = [p.text.strip() for p in content_div.find_all("p") if p.text.strip()]
        if paragraphs:
            content = "\n\n".join(paragraphs)
        else:
            content = content_div.text.strip()

    return {
        "title": real_title,
        "content": content,
        "next_url": ""
    }
