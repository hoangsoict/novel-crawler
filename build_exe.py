import sys
import subprocess
import os
import re

def preflight_check():
    """Validate GUI codebase before running PyInstaller to prevent TclError crashes."""
    print("🔍 Running Pre-flight Validation on GUI Codebase...")

    gui_path = os.path.abspath("src/gui.py")
    if not os.path.exists(gui_path):
        print(f"❌ PRE-FLIGHT CHECK FAILED: GUI source file not found at {gui_path}")
        sys.exit(1)

    # 1. Static Scan: Check for floating-point font sizes like 9.5 or 10.5 in font tuples
    with open(gui_path, "r", encoding="utf-8") as f:
        content = f.read()

    float_font_matches = re.findall(r'font\s*=\s*\([^)]*\d+\.\d+[^)]*\)', content)
    if float_font_matches:
        print("❌ PRE-FLIGHT CHECK FAILED: Detected floating-point font size in src/gui.py!")
        for match in float_font_matches:
            print(f"   -> Violating code: {match}")
        print("💡 Requirement: All Tkinter font sizes must be integers (e.g. 9 or 10, never 9.5).")
        sys.exit(1)

    # 2. Runtime Module Load Test: Instantiates GUI headlessly to ensure _tkinter initializes cleanly
    try:
        sys.path.insert(0, os.path.abspath("."))
        import tkinter as tk
        from src.gui import NovelCrawlerGUI

        root = tk.Tk()
        root.withdraw()
        app = NovelCrawlerGUI(root)
        root.destroy()
        print("✅ Pre-flight GUI validation PASSED! All fonts and widgets initialized cleanly.\n")
    except Exception as e:
        print(f"❌ PRE-FLIGHT CHECK FAILED: GUI runtime initialization error: {e}")
        sys.exit(1)

def build_executable():
    """Build standalone Windows EXE file using PyInstaller."""
    sys.stdout.reconfigure(encoding='utf-8')

    print("==================================================")
    print("      BUILDING NOVEL CRAWLER EXE WITH PYINSTALLER")
    print("==================================================")

    # Run mandatory preflight check
    preflight_check()

    # Check PyInstaller availability
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    icon_path = os.path.abspath("assets/icon.ico")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "NovelCrawler",
        "--clean",
    ]
    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])
    cmd.append("main.py")

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = os.path.abspath("dist/NovelCrawler/NovelCrawler.exe")
        print("\n==================================================")
        print("BUILD SUCCESSFUL!")
        print(f"Executable output path: {exe_path}")
        print("==================================================")
    else:
        print("\nBUILD FAILED! Check error log above.")

if __name__ == "__main__":
    build_executable()
