import argparse
import sys
import os

from .crawler.downloader import NovelDownloader

def run_cli():
    """CLI entry point for WikiCV Novel Crawler."""
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description="WikiCV Novel Crawler - Tải truyện từ wikicv.org thành file text.")
    parser.add_argument("--url", "-u", required=True, help="URL trang chủ truyện (vd: https://wikicv.org/truyen/...)")
    parser.add_argument("--out-dir", "-o", default="downloads", help="Thư mục xuất file text (Mặc định: downloads)")
    parser.add_argument("--cookie", "-c", default=None, help="Cookie đăng nhập tài khoản wikicv.org (Nếu bị hết lượt đọc)")
    parser.add_argument("--delay-min", type=float, default=1.0, help="Thời gian nghỉ tối thiểu giữa 2 chương (giây)")
    parser.add_argument("--delay-max", type=float, default=2.5, help="Thời gian nghỉ tối đa giữa 2 chương (giây)")
    parser.add_argument("--batch-size", type=int, default=50, help="Số chương tải liên tiếp trước khi nghỉ dài")
    parser.add_argument("--batch-delay-min", type=float, default=10.0, help="Thời gian nghỉ dài tối thiểu (giây)")
    parser.add_argument("--batch-delay-max", type=float, default=20.0, help="Thời gian nghỉ dài tối đa (giây)")

    args = parser.parse_args()

    print("==================================================")
    print("      WIKICV NOVEL CRAWLER - CLI MODE            ")
    print("==================================================")

    def log_cb(msg: str):
        print(f"{msg}")

    def progress_cb(cur: int, tot: int, title: str, status: str):
        percent = (cur / tot) * 100 if tot > 0 else 0
        sys.stdout.write(f"\r⏳ Tiến độ: [{cur}/{tot}] ({percent:.1f}%) - {title[:30]}")
        sys.stdout.flush()

    downloader = NovelDownloader(
        novel_url=args.url,
        output_dir=args.out_dir,
        cookie=args.cookie,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        batch_size=args.batch_size,
        batch_delay_min=args.batch_delay_min,
        batch_delay_max=args.batch_delay_max,
        log_callback=log_cb,
        progress_callback=progress_cb
    )

    try:
        out_file = downloader.download()
        print("\n==================================================")
        print(f"✅ Tải thành công! File lưu tại: {out_file}")
        print("==================================================")
    except KeyboardInterrupt:
        print("\n⚠️ Đã nhận tín hiệu dừng từ bàn phím (Ctrl+C). Tiến độ đã được lưu.")
    except Exception as e:
        print(f"\n❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    run_cli()
