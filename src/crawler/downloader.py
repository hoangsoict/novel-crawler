import time
import random
import threading
import os
import re
from typing import Callable, Optional, Dict, Any
import requests

from .parser import fetch_novel_info, fetch_chapter_list, fetch_chapter_content
from .storage import StorageManager
from .warp_utils import WarpManager

class NovelDownloader:
    """Manages chapter fetching loop, delays, retries, resume capability, and callbacks."""

    def __init__(
        self,
        novel_url: str,
        output_dir: str = "downloads",
        cookie: Optional[str] = None,
        delay_min: float = 1.0,
        delay_max: float = 2.5,
        batch_size: int = 50,
        batch_delay_min: float = 10.0,
        batch_delay_max: float = 20.0,
        max_retries: int = 3,
        enable_warp_reset: bool = True,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.novel_url = novel_url
        self.output_dir = os.path.abspath(output_dir)
        self.cookie = cookie
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.batch_size = batch_size
        self.batch_delay_min = batch_delay_min
        self.batch_delay_max = batch_delay_max
        self.max_retries = max_retries
        self.enable_warp_reset = enable_warp_reset
        self.progress_callback = progress_callback
        self.log_callback = log_callback

        self._pause_event = threading.Event()
        self._pause_event.set()  # Set means NOT paused
        self._cancel_flag = False

        self.session = requests.Session()
        if self.cookie and self.cookie.strip():
            self.session.headers.update({"Cookie": self.cookie.strip()})

    def log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)

    def pause(self) -> None:
        self._pause_event.clear()
        self.log("⏸️ Đã nhận lệnh TẠM DỪNG...")

    def resume(self) -> None:
        self._pause_event.set()
        self.log("▶️ Tiếp tục tải...")

    def cancel(self) -> None:
        self._cancel_flag = True
        self._pause_event.set()  # Unblock if paused
        self.log("⏹️ Đã nhận lệnh HỦY TẢI.")

    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def is_cancelled(self) -> bool:
        return self._cancel_flag

    def download(self) -> str:
        """
        Execute full download workflow.
        Returns final output text file path.
        """
        # Clean URL fragments like #! or trailing slashes
        clean_url = self.novel_url.split('#')[0].rstrip('/')
        self.novel_url = clean_url

        self.log(f"🔍 Đang truy cập trang thông tin truyện: {self.novel_url}")
        info = fetch_novel_info(self.session, self.novel_url)
        book_id = info["book_id"]
        sign_key = info["sign_key"]
        split_idx = info.get("split_idx", 35)
        title = info["title"]
        synopsis = info["synopsis"]

        self.log(f"📖 Tên truyện: {title}")
        self.log(f"🔑 Book ID: {book_id}")

        # Store cache inside the chosen download directory under .cache/
        cache_base_path = os.path.join(self.output_dir, ".cache")
        storage = StorageManager(book_id, base_cache_dir=cache_base_path)
        self.log(f"📂 Thư mục lưu tiến trình cache: {storage.cache_dir}")

        # Check existing progress or fetch new chapter list
        self.log("📋 Đang lấy mục lục danh sách toàn bộ chương...")
        chapter_list = fetch_chapter_list(self.session, book_id, sign_key, self.novel_url, split_idx=split_idx)
        
        if not chapter_list:
            self.log("⚠️ Không lấy được mục lục từ API hoặc HTML, đang mở chế độ nạp chương tự động theo luồng...")
            chap1_url = f"{self.novel_url}/chuong-1"
            chapter_list = [{"title": "Chương 1", "url": chap1_url}]

        if len(chapter_list) == 1:
            self.log("ℹ️ Truyện này sẽ tự động vừa tải vừa nạp nối tiếp từng chương ('Chương sau') cho đến chương cuối cùng...")

        total_chapters = len(chapter_list)
        self.log(f"📚 Số chương khởi tạo ban đầu: {total_chapters}")

        # ALWAYS check existing progress file inside output_dir/.cache/<book_id>/progress.json
        progress_data = storage.load_progress() or {
            "book_id": book_id,
            "title": title,
            "novel_url": self.novel_url,
            "synopsis": synopsis,
            "output_dir": self.output_dir,
            "total_chapters": total_chapters,
            "downloaded_indices": []
        }

        downloaded_set = set(progress_data.get("downloaded_indices", []))
        
        # Determine the last downloaded chapter index
        max_cached = max(downloaded_set) if downloaded_set else 0
        
        # Verify BOTH <max_chapter:05d>.json cache AND output .txt file for the last downloaded chapter
        if max_cached > 0:
            last_chap_title = chapter_list[max_cached - 1]["title"] if max_cached <= len(chapter_list) else f"Chương {max_cached}"
            cached_info = storage.get_cached_chapter(max_cached)
            content_snippet = ""
            if cached_info and isinstance(cached_info, dict):
                if cached_info.get("title"):
                    last_chap_title = cached_info.get("title")
                content_snippet = cached_info.get("content", "").strip()[:40]

            # 1. Verify JSON cache validity
            if not storage.verify_chapter_validity(max_cached):
                self.log(f"⚠️ Phát hiện chương cuối (Chương {max_cached}) bị rỗng/lỗi cache do ngắt đột ngột trước đó. Tự động xóa cache lỗi để tải lại!")
                storage.remove_chapter_cache(max_cached)
                downloaded_set.discard(max_cached)
                progress_data["downloaded_indices"] = sorted(list(downloaded_set))
                storage.save_progress(progress_data)
                max_cached = max(downloaded_set) if downloaded_set else 0
            else:
                # 2. Verify output .txt file contains BOTH chapter title AND actual content snippet
                txt_ok = storage.verify_txt_has_chapter(self.output_dir, title, last_chap_title, content_snippet)
                if not txt_ok:
                    self.log(f"⚠️ Phát hiện file .txt chưa có nội dung Chương {max_cached} ({last_chap_title}). Tự động đồng bộ xuất lại file .txt đầy đủ!")
                    try:
                        storage.export_full_text(self.output_dir, title, synopsis, chapter_list)
                        self.log(f"✅ Đã xuất đồng bộ lại file .txt đầy đủ từ 1 đến Chương {max_cached} thành công!")
                    except Exception as e:
                        self.log(f"⚠️ Lỗi đồng bộ file .txt: {e}")
                else:
                    self.log(f"🔍 ĐÃ KIỂM TRA ĐỐI CHIẾU CHƯƠNG CUỐI (Chương {max_cached}): File JSON cache & File .txt đều đầy đủ 100%!")

        if max_cached > 0:
            next_start_idx = max_cached + 1
            self.log(f"⚡ TỰ ĐỘNG BỎ QUA {max_cached} CHƯƠNG ĐÃ TẢI ➔ NHẢY BẮT ĐẦU TẢI NGAY TỪ CHƯƠNG {next_start_idx}!")
            if self.progress_callback:
                self.progress_callback(
                    max_cached,
                    len(chapter_list),
                    chapter_list[max_cached - 1]["title"],
                    chapter_list[max_cached - 1].get("volume", ""),
                    f"✅ Đã đối chiếu 1-{max_cached} chương (Tải tiếp từ Ch.{next_start_idx})"
                )
            idx = next_start_idx
        else:
            self.log("🆕 Chưa có tiến trình trong thư mục này. Bắt đầu tải mới từ Chương 1.")
            idx = 1

        chapters_downloaded_in_session = 0
        known_urls = {c["url"] for c in chapter_list}

        while idx <= len(chapter_list):
            if self.is_cancelled():
                self.log("❌ Quá trình tải đã bị hủy bởi người dùng.")
                break

            # Wait if paused
            while not self._pause_event.is_set():
                if self.is_cancelled():
                    break
                time.sleep(0.5)

            if self.is_cancelled():
                break

            chap_info = chapter_list[idx - 1]
            chap_title = chap_info["title"]
            chap_url = chap_info["url"]

            # Double check if chapter is already cached
            cached = storage.get_cached_chapter(idx)
            if idx in downloaded_set and cached:
                idx += 1
                continue

            # Fetch chapter content with retry logic
            success = False
            last_err = ""
            for attempt in range(1, self.max_retries + 1):
                if self.is_cancelled():
                    break
                try:
                    self.log(f"⬇️ [{idx}/{len(chapter_list)}] Đang tải: {chap_title}")
                    chap_data = fetch_chapter_content(self.session, chap_url)
                    
                    real_title = chap_data.get("title")
                    if real_title:
                        chap_title = real_title
                        chapter_list[idx - 1]["title"] = chap_title

                    chap_vol = chap_info.get("volume", "")
                    storage.save_chapter(idx, chap_title, chap_data["content"], volume=chap_vol)

                    downloaded_set.add(idx)
                    progress_data["downloaded_indices"] = sorted(list(downloaded_set))
                    progress_data["total_chapters"] = len(chapter_list)
                    progress_data["chapter_list"] = chapter_list
                    storage.save_progress(progress_data)
                    
                    # Update output .txt file live inside output_dir
                    try:
                        storage.export_full_text(self.output_dir, title, synopsis, chapter_list)
                    except Exception:
                        pass

                    success = True
                    chapters_downloaded_in_session += 1
                    break
                except Exception as e:
                    last_err = str(e)
                    self.log(f"⚠️ Lỗi tải chương {idx} (Lần {attempt}/{self.max_retries}): {e}")
                    if attempt < self.max_retries:
                        sleep_time = random.uniform(3.0, 7.0)
                        self.log(f"⏳ Tự động nghỉ {sleep_time:.1f}s trước khi thử lại...")
                        time.sleep(sleep_time)

            # If standard retries failed, attempt Cloudflare WARP Reset if enabled
            if not success and not self.is_cancelled() and self.enable_warp_reset:
                if WarpManager.is_warp_installed():
                    self.log(f"🔄 Gặp lỗi không tải được chương {idx} ({chap_title}). Tiến hành Reset DNS Cloudflare WARP (Tắt -> Bật)...")
                    if WarpManager.reconnect_warp(log_callback=self.log):
                        self.log(f"⚡ Cloudflare WARP đã Connected! Đang thử tải lại chương {idx}...")
                        time.sleep(2.0)
                        # Mini retry after WARP reconnect
                        for warp_attempt in range(1, 3):
                            if self.is_cancelled():
                                break
                            try:
                                chap_data = fetch_chapter_content(self.session, chap_url)
                                real_title = chap_data.get("title")
                                if real_title:
                                    chap_title = real_title
                                    chapter_list[idx - 1]["title"] = chap_title

                                chap_vol = chap_info.get("volume", "")
                                storage.save_chapter(idx, chap_title, chap_data["content"], volume=chap_vol)

                                downloaded_set.add(idx)
                                progress_data["downloaded_indices"] = sorted(list(downloaded_set))
                                progress_data["total_chapters"] = len(chapter_list)
                                progress_data["chapter_list"] = chapter_list
                                storage.save_progress(progress_data)

                                try:
                                    storage.export_full_text(self.output_dir, title, synopsis, chapter_list)
                                except Exception:
                                    pass

                                success = True
                                chapters_downloaded_in_session += 1
                                self.log(f"🎉 Tải lại chương {idx} thành công sau khi Reset Cloudflare WARP!")
                                break
                            except Exception as e:
                                last_err = str(e)
                                self.log(f"⚠️ Thử lại sau WARP reset (Lần {warp_attempt}/2) thất bại: {e}")
                                time.sleep(3.0)

            if not success and not self.is_cancelled():
                self.log(f"🛑 ĐÃ DỪNG TIẾN TRÌNH: Không thể tải chương {idx} ({chap_title}) dù đã thử lại & Reset Cloudflare WARP.")
                self.log(f"💾 Tiến trình đã được lưu an toàn đến Chương {idx-1}. Bạn có thể khắc phục sự cố và bấm Start download để tải tiếp!")
                raise RuntimeError(f"Tải thất bại tại chương {idx} ({chap_title}): {last_err}")

            if self.progress_callback:
                chap_vol = chap_info.get("volume", "")
                self.progress_callback(idx, len(chapter_list), chap_title, chap_vol, f"Đã tải xong ({idx}/{len(chapter_list)})")

            # Delays for rate limiting
            if not self.is_cancelled() and idx < len(chapter_list):
                # Check long delay batch
                if chapters_downloaded_in_session > 0 and chapters_downloaded_in_session % self.batch_size == 0:
                    long_delay = random.uniform(self.batch_delay_min, self.batch_delay_max)
                    self.log(f"☕ Đã tải {chapters_downloaded_in_session} chương trong lượt này. Cho hệ thống nghỉ dài {long_delay:.1f}s chống rate-limit...")
                    time.sleep(long_delay)
                else:
                    short_delay = random.uniform(self.delay_min, self.delay_max)
                    time.sleep(short_delay)

            idx += 1

        self.log("💾 Đang tổng hợp toàn bộ các chương thành 1 file text duy nhất...")
        output_file = storage.export_full_text(self.output_dir, title, synopsis, chapter_list)
        
        # Automatically move completed file to "Finish" subfolder
        final_file = storage.move_to_finish(output_file)
        self.log(f"📁 TỰ ĐỘNG CHUYỂN FILE HOÀN THÀNH VÀO THƯ MỤC CON 'Finish':")
        self.log(f"🎉 HOÀN THÀNH 100%! File truyện đã được lưu tại:\n👉 {final_file}")
        
        return final_file
