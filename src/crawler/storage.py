import os
import json
import re
from typing import Dict, Any, List, Optional

def sanitize_filename(name: str) -> str:
    """Sanitize string for Windows filename safety."""
    # Replace illegal characters for Windows filenames
    sanitized = re.sub(r'[\\/*?:"<>|]', "", name)
    sanitized = sanitized.strip().strip('.')
    return sanitized if sanitized else "truyen_output"

class StorageManager:
    """Manages cache directory, progress saving, chapter caching, and exporting final file."""

    def __init__(self, book_id: str, base_cache_dir: str = ".cache"):
        self.book_id = book_id
        self.cache_dir = os.path.join(base_cache_dir, book_id)
        self.chapters_dir = os.path.join(self.cache_dir, "chapters")
        self.progress_file = os.path.join(self.cache_dir, "progress.json")

        os.makedirs(self.chapters_dir, exist_ok=True)

    def load_progress(self) -> Optional[Dict[str, Any]]:
        """Load progress JSON if exists."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def save_progress(self, progress_data: Dict[str, Any]) -> None:
        """Save progress JSON."""
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    def save_chapter(self, index: int, title: str, content: str, volume: str = "") -> str:
        """Save individual chapter text file in cache."""
        filename = f"{index:05d}.json"
        filepath = os.path.join(self.chapters_dir, filename)
        data = {
            "index": index,
            "title": title,
            "volume": volume,
            "content": content
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    def get_cached_chapter(self, index: int) -> Optional[Dict[str, Any]]:
        """Get cached chapter content if exists."""
        filename = f"{index:05d}.json"
        filepath = os.path.join(self.chapters_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def verify_chapter_validity(self, index: int) -> bool:
        """Verify if cached chapter JSON file exists, is valid JSON, and has valid content."""
        cached = self.get_cached_chapter(index)
        if not cached or not isinstance(cached, dict):
            return False
        content = cached.get("content", "")
        if not content or not isinstance(content, str):
            return False
        content_clean = content.strip()
        if len(content_clean) < 30 or content_clean == "[Chương này chưa tải được nội dung]":
            return False
        return True

    def remove_chapter_cache(self, index: int) -> None:
        """Remove invalid chapter JSON cache file."""
        filename = f"{index:05d}.json"
        filepath = os.path.join(self.chapters_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

    def verify_txt_has_chapter(self, output_dir: str, title: str, chapter_title: str, content_snippet: str = "") -> bool:
        """Check if the output .txt file exists (in output_dir or Finish subfolder) and contains content."""
        safe_title = sanitize_filename(title)
        out_filepath = os.path.join(output_dir, f"{safe_title}.txt")
        finish_filepath = os.path.join(output_dir, "Finish", f"{safe_title}.txt")

        target_path = finish_filepath if os.path.exists(finish_filepath) else out_filepath
        if not os.path.exists(target_path):
            return False
        try:
            if os.path.getsize(target_path) == 0:
                return False
            with open(target_path, "r", encoding="utf-8") as f:
                txt_content = f.read()

            if not chapter_title or chapter_title not in txt_content:
                return False

            if content_snippet:
                clean_snippet = content_snippet.strip()[:40]
                if clean_snippet and clean_snippet not in txt_content:
                    return False

            return True
        except Exception:
            return False

    def move_to_finish(self, output_file: str) -> str:
        """Move finished .txt file to 'Finish' subfolder inside output directory."""
        if not os.path.exists(output_file):
            return output_file
        import shutil
        output_dir = os.path.dirname(output_file)
        filename = os.path.basename(output_file)
        finish_dir = os.path.join(output_dir, "Finish")
        os.makedirs(finish_dir, exist_ok=True)
        dest_filepath = os.path.join(finish_dir, filename)

        if os.path.exists(dest_filepath):
            try:
                os.remove(dest_filepath)
            except Exception:
                pass
        shutil.move(output_file, dest_filepath)
        return dest_filepath

    def export_full_text(self, output_dir: str, title: str, synopsis: str, chapter_list: List[Dict[str, str]]) -> str:
        """
        Assemble all VALID cached chapters into the final combined text file.
        Only exports chapters that have actually been downloaded and cached.
        """
        os.makedirs(output_dir, exist_ok=True)
        safe_title = sanitize_filename(title)
        out_filepath = os.path.join(output_dir, f"{safe_title}.txt")

        with open(out_filepath, "w", encoding="utf-8") as f:
            # Write Header / Synopsis
            f.write("Giới thiệu :\n")
            f.write(synopsis.strip())
            f.write("\n\n" + "=" * 40 + "\n\n")

            # Write ONLY cached chapters sequentially
            last_volume = ""
            for idx, chap_info in enumerate(chapter_list, 1):
                cached_chap = self.get_cached_chapter(idx)
                if not cached_chap:
                    continue

                content = cached_chap.get("content", "").strip()
                if not content or content == "[Chương này chưa tải được nội dung]":
                    continue

                chap_title = cached_chap.get("title") or chap_info.get("title", f"Chương {idx}")
                volume = chap_info.get("volume", "").strip()

                if volume and volume != last_volume:
                    f.write(f"========================================\nPHẦN: {volume}\n========================================\n\n")
                    last_volume = volume

                f.write(f"{chap_title}\n\n")
                f.write(f"{content}\n\n")
                f.write("=" * 40 + "\n\n")

        return out_filepath
