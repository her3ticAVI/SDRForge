#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import time
import webbrowser

LAB_NAME = "IMSI Catcher"
LAB_DESC = "Software-only IMSI catcher simulator with rogue tower detection and RF visualization."

URL = "http://127.0.0.1:5055"


def find_root() -> Path:
    here = Path(__file__).resolve()

    for parent in here.parents:
        if (parent / "configs").exists():
            return parent

    return here.parents[2]


def run_lab():
    root = find_root()
    app_path = root / "configs" / "IMSI_catcher" / "app.py"

    if not app_path.exists():
        print(f"[ERROR] Missing app file: {app_path}")
        input("Press Enter to return...")
        return

    proc = subprocess.Popen(
        [sys.executable, str(app_path)],
        cwd=str(app_path.parent),
    )

    time.sleep(1)
    webbrowser.open_new(URL)

    proc.wait()


def run():
    run_lab()


def launch():
    run_lab()


if __name__ == "__main__":
    run_lab()