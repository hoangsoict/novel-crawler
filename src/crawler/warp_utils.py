import time
import shutil
import subprocess
import os
from typing import Optional, Callable

class WarpManager:
    """Utility class to manage Cloudflare WARP CLI (warp-cli) connection reset on Windows."""

    @staticmethod
    def get_warp_cli_path() -> Optional[str]:
        """Find warp-cli executable path."""
        path = shutil.which("warp-cli")
        if path:
            return path
        
        default_path = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
        if os.path.exists(default_path):
            return default_path
            
        return None

    @classmethod
    def is_warp_installed(cls) -> bool:
        """Check if warp-cli is available on system."""
        return cls.get_warp_cli_path() is not None

    @classmethod
    def get_warp_status(cls) -> str:
        """Get current WARP connection status."""
        cli_path = cls.get_warp_cli_path()
        if not cli_path:
            return "Not Installed"
        try:
            res = subprocess.run(
                [cli_path, "status"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            stdout = res.stdout.strip()
            if "Connected" in stdout:
                return "Connected"
            elif "Disconnected" in stdout:
                return "Disconnected"
            elif "Connecting" in stdout:
                return "Connecting"
            return stdout if stdout else "Unknown"
        except Exception as e:
            return f"Error: {e}"

    @classmethod
    def is_connected(cls) -> bool:
        """Check if WARP status is Connected."""
        return cls.get_warp_status() == "Connected"

    @classmethod
    def reconnect_warp(cls, timeout: int = 20, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disconnect and reconnect Cloudflare WARP, waiting until status becomes 'Connected'.
        Returns True if reconnected successfully within timeout, False otherwise.
        """
        cli_path = cls.get_warp_cli_path()
        if not cli_path:
            if log_callback:
                log_callback("⚠️ Không tìm thấy warp-cli.exe trên hệ thống để reset Cloudflare WARP!")
            return False

        def log(msg: str):
            if log_callback:
                log_callback(msg)

        log("🔄 Đang thực hiện tắt Cloudflare WARP (warp-cli disconnect)...")
        try:
            subprocess.run(
                [cli_path, "disconnect"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except Exception as e:
            log(f"⚠️ Lỗi khi disconnect WARP: {e}")

        time.sleep(1.5)

        log("⚡ Đang bật lại Cloudflare WARP (warp-cli connect)...")
        try:
            subprocess.run(
                [cli_path, "connect"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except Exception as e:
            log(f"⚠️ Lỗi khi connect WARP: {e}")

        log("⏳ Đang chờ Cloudflare WARP chuyển sang trạng thái Connected...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = cls.get_warp_status()
            if status == "Connected":
                log("✅ Cloudflare WARP đã chuyển sang trạng thái Connected!")
                return True
            time.sleep(1.0)

        log(f"❌ WARP chưa thể kết nối lại sau {timeout}s (Trạng thái hiện tại: {cls.get_warp_status()})")
        return False
