#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


APP_VERSION = "0.1.0"

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent
LABS_DIR = PROJECT_ROOT / "framework" / "labs"
IMAGES_DIR = PROJECT_ROOT / "images"

LOGO_ANSI = IMAGES_DIR / "logo.ans"


def ensure_dependencies() -> None:
    missing: List[str] = []
    try:
        import textual  # noqa: F401
    except Exception:
        missing.append("textual")

    try:
        import rich  # noqa: F401
    except Exception:
        missing.append("rich")

    if missing:
        print("\n[SDRForge] Missing Python dependencies:\n  - " + "\n  - ".join(missing))
        print("\nInstall with:\n  python3 -m pip install -U " + " ".join(missing) + "\n")
        sys.exit(1)


@dataclass(frozen=True)
class LabInfo:
    name: str
    desc: str
    file: Path


def discover_labs() -> List[LabInfo]:
    labs: List[LabInfo] = []
    if not LABS_DIR.exists():
        return labs

    for py in sorted(LABS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue
        labs.append(
            LabInfo(
                name=py.stem.replace("_", " "),
                desc="Executable SDRForge lab",
                file=py,
            )
        )
    return labs


def load_logo_rich_text():
    from rich.text import Text

    if not LOGO_ANSI.exists():
        return Text("")

    raw = LOGO_ANSI.read_text(errors="ignore")
    try:
        return Text.from_ansi(raw)
    except Exception:
        return Text(raw)


def run_menu_once(labs: List[LabInfo]) -> Optional[LabInfo]:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Footer, Header, ListItem, ListView, Static
    from textual import events

    class MenuApp(App):
        TITLE = "SDRForge"
        SUB_TITLE = "Framework"

        CSS = """
        Screen { layout: vertical; padding: 0; }
        #logo_panel { height: 16; content-align: center middle; padding: 0 1; }
        #logo { width: 100%; height: 100%; content-align: center middle; }
        #body { height: 1fr; }
        #left { width: 44; border: round #666666; padding: 0 1; }
        #right { width: 1fr; border: round #666666; padding: 0 1; }
        #lab_list { height: 1fr; }
        #details { height: 1fr; }
        #footer_hint { height: 1; padding: 0 1; }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("enter", "launch", "Launch"),
            ("b", "quit", "Back"),
        ]

        def __init__(self, labs: List[LabInfo]):
            super().__init__()
            self.labs = labs
            self.selected: Optional[LabInfo] = None
            self._logo_text = load_logo_rich_text()

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(self._logo_text, id="logo_panel")

            with Horizontal(id="body"):
                with Vertical(id="left"):
                    yield Static("[b]Labs[/b]")
                    self.list_view = ListView(id="lab_list")
                    yield self.list_view

                with Vertical(id="right"):
                    yield Static("[b]Description[/b]", id="details")

            yield Static("Enter=launch   q=quit   ↑/↓=navigate", id="footer_hint")
            yield Footer()

        async def on_mount(self) -> None:
            items: List[ListItem] = []
            for lab in self.labs:
                items.append(ListItem(Static(lab.name)))
            await self.list_view.extend(items)

            if self.labs:
                self.list_view.index = 0
                self._update_details(0)

        def _update_details(self, idx: int) -> None:
            details = self.query_one("#details", Static)
            if 0 <= idx < len(self.labs):
                lab = self.labs[idx]
                details.update(
                    "[b]Description[/b]\n"
                    f"{lab.desc}\n\n"
                    f"File: {lab.file}\n"
                )
            else:
                details.update("[b]Description[/b]\n(no selection)\n")

        def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
            self._update_details(event.list_view.index or 0)

        def on_list_view_selected(self, event: ListView.Selected) -> None:
            idx = event.list_view.index or 0
            if 0 <= idx < len(self.labs):
                self.selected = self.labs[idx]
                self.exit(result=self.selected)

        def action_launch(self) -> None:
            idx = self.list_view.index or 0
            if 0 <= idx < len(self.labs):
                self.selected = self.labs[idx]
                self.exit(result=self.selected)

        def on_key(self, event: events.Key) -> None:
            if event.key == "enter":
                event.prevent_default()
                event.stop()
                self.action_launch()

    app = MenuApp(labs)
    return app.run()


def run_waveform_quiz(lab: LabInfo) -> None:
    print("\n================ SDR WAVEFORM QUIZ ================\n")
    print("Topic: Doorbell RF burst capture (waveform concepts)\n")

    questions = [
        (
            "1) What does sample rate control?",
            ["A) Tune frequency", "B) Captured bandwidth", "C) Antenna gain", "D) Transmit power"],
            "B",
            "Sample rate determines the bandwidth captured around the center frequency.",
        ),
        (
            "2) What are IQ samples?",
            ["A) Microphone audio", "B) Two antennas", "C) Complex baseband (I + jQ)", "D) Packet headers"],
            "C",
            "IQ is complex baseband data after downconversion.",
        ),
        (
            "3) Doorbells commonly look like what on RF captures?",
            ["A) FM voice", "B) OOK/ASK burst", "C) WiFi OFDM", "D) Bluetooth hopping"],
            "B",
            "Many doorbells use simple amplitude-keyed bursts (OOK/ASK).",
        ),
        (
            "4) In an amplitude envelope plot, an OOK burst appears as:",
            ["A) Flat line", "B) Smooth sine wave", "C) Spike above noise", "D) Only random noise"],
            "C",
            "OOK bursts show clear amplitude spikes above the noise floor.",
        ),
        (
            "5) Too much gain usually causes:",
            ["A) Higher noise floor / possible clipping", "B) Lower sample rate", "C) Frequency shift", "D) Real-only IQ"],
            "A",
            "Excess gain raises noise and can distort/clamp the signal.",
        ),
    ]

    score = 0
    for q, options, ans, explain in questions:
        print(q)
        for opt in options:
            print("   " + opt)
        user = input("\nYour answer (A/B/C/D): ").strip().upper()
        if user == ans:
            print("✔ Correct")
            score += 1
        else:
            print("✘ Incorrect")
        print(explain)
        print("\n---------------------------------------------\n")

    print(f"Final Score: {score}/{len(questions)}")
    input("Press Enter to launch the lab...\n")


def launch_lab(lab: LabInfo) -> int:
    if not lab.file.exists():
        print(f"[SDRForge] Lab not found: {lab.file}")
        return 1

    if "doorbell" in lab.name.lower():
        run_waveform_quiz(lab)

    env = os.environ.copy()
    env["SDRFORGE_ROOT"] = str(PROJECT_ROOT)
    env["SDRFORGE_IMAGES"] = str(IMAGES_DIR)
    env["SDRFORGE_LABS"] = str(LABS_DIR)

    return subprocess.call([sys.executable, str(lab.file)], env=env)


def main() -> None:
    ensure_dependencies()

    if not LABS_DIR.exists():
        print(f"[SDRForge] Labs directory not found: {LABS_DIR}")
        sys.exit(1)

    while True:
        labs = discover_labs()
        if not labs:
            print(f"[SDRForge] No labs found in: {LABS_DIR}")
            sys.exit(0)

        selected = run_menu_once(labs)
        if selected is None:
            break

        _ = launch_lab(selected)

    sys.exit(0)


if __name__ == "__main__":
    main()
