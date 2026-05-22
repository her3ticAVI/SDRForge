#!/usr/bin/env python3
from __future__ import annotations

LAB_NAME = "Doorbell Relay"

LAB_DESC = (
    "Software-only OOK/ASK wireless doorbell simulation.\n\n"
    "Includes:\n"
    "- GNU Radio visualization\n"
    "- Waterfall analysis\n"
    "- Simulated RF bursts\n"
    "- Signal replay concepts"
)

import sys
import shutil
import subprocess
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent.parent

CONFIG_DIR = PROJECT_ROOT / "configs"

GRC_FILE = CONFIG_DIR / "Radio_relay.grc"
PY_FLOWGRAPH = CONFIG_DIR / "Radio_relay.py"


def find_gnuradio_companion() -> str | None:
    for cmd in [
        "gnuradio-companion",
        "gnuradio-companion-3.10",
    ]:
        path = shutil.which(cmd)

        if path:
            return path

    return None


def run_python_flowgraph() -> int:
    if not PY_FLOWGRAPH.exists():
        print(f"\nMissing:\n{PY_FLOWGRAPH}\n")
        return 1

    return subprocess.call(
        [sys.executable, str(PY_FLOWGRAPH)]
    )


def open_grc_file() -> int:
    grc = find_gnuradio_companion()

    if grc is None:
        print("\nGNU Radio Companion not found.\n")
        return 1

    if not GRC_FILE.exists():
        print(f"\nMissing:\n{GRC_FILE}\n")
        return 1

    return subprocess.call(
        [grc, str(GRC_FILE)]
    )


def run() -> None:
    from textual.app import App, ComposeResult
    from textual.widgets import (
        Button,
        Footer,
        Header,
        Static,
    )
    from textual.containers import Vertical

    class DoorbellLabApp(App):
        TITLE = "SDRForge"
        SUB_TITLE = "Doorbell Lab"

        CSS = """
        Screen {
            align: center middle;
        }

        #box {
            width: 70;
            border: round #666666;
            padding: 1 2;
        }

        Button {
            width: 100%;
            margin: 1 0;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("b", "quit", "Back"),
        ]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)

            with Vertical(id="box"):

                yield Static(
                    "[b]Doorbell Signal Lab[/b]\n\n"
                    "Software-only OOK/ASK simulation.\n"
                )

                yield Button(
                    "See the Signal",
                    id="signal",
                    variant="success",
                )

                yield Button(
                    "How It's Done",
                    id="grc",
                    variant="primary",
                )

                yield Button(
                    "Back",
                    id="back",
                )

            yield Footer()

        def on_button_pressed(
            self,
            event: Button.Pressed,
        ) -> None:

            if event.button.id == "signal":
                self.exit("signal")

            elif event.button.id == "grc":
                self.exit("grc")

            elif event.button.id == "back":
                self.exit("back")

    while True:

        choice = DoorbellLabApp().run()

        if choice == "signal":
            run_python_flowgraph()
            continue

        if choice == "grc":
            open_grc_file()
            continue

        break


if __name__ == "__main__":
    run()