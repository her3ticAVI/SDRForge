#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


LAB_NAME = "Radio"

LAB_DESC = (
    "Starter sandbox lab for experimenting with GNU Radio.\n\n"
    "Includes:\n"
    "- Open a blank GNU Radio Companion workspace\n"
    "- Build your own radio flowgraph\n"
    "- Prototype SDRForge ideas safely"
)


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = Path(os.environ.get("SDRFORGE_ROOT", THIS_FILE.parent.parent.parent)).resolve()

LAB0_GRC = PROJECT_ROOT / "configs" / "Lab0_blank.grc"


def find_gnuradio_companion() -> str | None:
    for cmd in ["gnuradio-companion", "gnuradio-companion-3.10"]:
        path = shutil.which(cmd)
        if path:
            return path
    return None


def open_gnuradio() -> int:
    grc = find_gnuradio_companion()

    if grc is None:
        print("\n[SDRForge] GNU Radio Companion not found.")
        print("Install with:")
        print("  sudo apt install gnuradio\n")
        return 1

    if not LAB0_GRC.exists():
        LAB0_GRC.parent.mkdir(parents=True, exist_ok=True)
        LAB0_GRC.touch()

    return subprocess.call([grc, str(LAB0_GRC)])


def run() -> None:
    from textual.app import App, ComposeResult
    from textual.widgets import Button, Footer, Header, Static
    from textual.containers import Vertical

    class Lab0App(App):
        TITLE = "SDRForge"
        SUB_TITLE = "Lab0"

        CSS = """
        Screen { align: center middle; }

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
                    "[b]Lab0[/b]\n\n"
                    "Experiment building your own radio here.\n"
                )

                yield Button("GNU Radio", id="gnuradio", variant="primary")
                yield Button("Back", id="back")

            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "gnuradio":
                self.exit("gnuradio")
            elif event.button.id == "back":
                self.exit("back")

    while True:
        choice = Lab0App().run()

        if choice == "gnuradio":
            open_gnuradio()
            continue

        break


if __name__ == "__main__":
    run()