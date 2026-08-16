import sys
import os

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.cli import run_cli
from src.gui import run_gui

def main():
    """Main application entrypoint."""
    # Check if CLI parameters were passed
    if len(sys.argv) > 1 and any(arg in sys.argv for arg in ["--url", "-u", "--help", "-h"]):
        run_cli()
    else:
        run_gui()

if __name__ == "__main__":
    main()
