#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

LAB_NAME = "ADS-B Aircraft Tracker"

LAB_DESC = (
    "Live software-only aircraft tracking lab.\n"
    "Features: Real aircraft positions - Live map tracking - Callsign / altitude / speed - Software-only operation \n"
    "Educational Focus: ADS-B aircraft tracking - Aircraft transponders - Aviation surveillance systems"
)


def run():
    here = Path(__file__).resolve()
    project_root = here.parents[2]

    server = project_root / "configs" / "adsb_tracker" / "adsb_server.py"

    if not server.exists():
        print(f"[!] Missing file: {server}")
        input("Press Enter to return...")
        return

    print("[*] Launching ADS-B Aircraft Tracker...")
    print(f"[*] Server: {server}")
    print("[*] Browser should open at http://127.0.0.1:5055")
    print()

    try:
        subprocess.run(
            [sys.executable, str(server)],
            cwd=str(server.parent),
            check=False
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[!] Failed to launch ADS-B lab: {e}")
        input("Press Enter to return...")


def main():
    run()


def launch():
    run()


if __name__ == "__main__":
    run()