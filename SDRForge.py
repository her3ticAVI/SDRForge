#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import subprocess
import importlib.util

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


THIS_FILE = Path(__file__).resolve()


def find_project_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        labs_dir = path / "framework" / "labs"

        if labs_dir.exists() and labs_dir.is_dir():
            return path

    print("[SDRForge] Could not find project root.")
    sys.exit(1)


PROJECT_ROOT = find_project_root(THIS_FILE.parent)

LABS_DIR = PROJECT_ROOT / "framework" / "labs"
IMAGES_DIR = PROJECT_ROOT / "images"
LOGO_ANSI = IMAGES_DIR / "logo.ans"


@dataclass(frozen=True)
class LabInfo:
    name: str
    desc: str
    file: Path


def load_lab_metadata(py: Path) -> tuple[str, str]:
    name = py.stem.replace("_", " ")
    desc = "No description available."

    try:
        module_name = f"sdrforge_lab_{py.stem}"
        spec = importlib.util.spec_from_file_location(module_name, py)

        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            name = str(getattr(module, "LAB_NAME", name))
            desc = str(getattr(module, "LAB_DESC", desc))

    except Exception:
        pass

    return name, desc


def discover_labs() -> List[LabInfo]:
    labs: List[LabInfo] = []

    if not LABS_DIR.exists():
        return labs

    for py in sorted(LABS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue

        if py.name == "SDRForge.py":
            continue

        name, desc = load_lab_metadata(py)

        labs.append(
            LabInfo(
                name=name,
                desc=desc,
                file=py,
            )
        )

    return labs


def load_logo():
    from rich.text import Text

    if not LOGO_ANSI.exists():
        return Text("SDRForge")

    raw = LOGO_ANSI.read_text(errors="ignore")

    try:
        return Text.from_ansi(raw)
    except Exception:
        return Text(raw)


def run_menu(labs: List[LabInfo]) -> Optional[LabInfo]:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Footer, Header, ListItem, ListView, Static
    from textual import events

    class MenuApp(App):
        TITLE = "SDRForge"

        CSS = """
        Screen {
            layout: vertical;
        }

        #logo_panel {
            height: 16;
            content-align: center middle;
        }

        #body {
            height: 1fr;
        }

        #left {
            width: 40;
            border: round #666666;
            padding: 0 1;
        }

        #right {
            width: 1fr;
            border: round #666666;
            padding: 0 1;
        }

        #lab_list {
            height: 1fr;
        }

        #details {
            height: 1fr;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("enter", "launch", "Launch"),
        ]

        def __init__(self, labs: List[LabInfo]):
            super().__init__()
            self.labs = labs
            self.selected: Optional[LabInfo] = None
            self.logo = load_logo()

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)

            yield Static(self.logo, id="logo_panel")

            with Horizontal(id="body"):
                with Vertical(id="left"):
                    yield Static("[b]Labs[/b]")
                    self.list_view = ListView(id="lab_list")
                    yield self.list_view

                with Vertical(id="right"):
                    yield Static("", id="details")

            yield Footer()

        async def on_mount(self) -> None:
            items = []

            for lab in self.labs:
                items.append(ListItem(Static(lab.name)))

            await self.list_view.extend(items)

            if self.labs:
                self.list_view.index = 0
                self.update_details(0)

        def update_details(self, idx: int) -> None:
            details = self.query_one("#details", Static)

            if 0 <= idx < len(self.labs):
                lab = self.labs[idx]

                details.update(
                    f"[b]{lab.name}[/b]\n\n"
                    f"{lab.desc}\n\n"
                    f"[dim]{lab.file}[/dim]"
                )
            else:
                details.update("[b]SDRForge[/b]\n\nSelect a lab.")

        def on_list_view_highlighted(
            self,
            event: ListView.Highlighted,
        ) -> None:
            idx = event.list_view.index or 0
            self.update_details(idx)

        def on_list_view_selected(
            self,
            event: ListView.Selected,
        ) -> None:
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


def launch_lab(lab: LabInfo) -> int:
    if not lab.file.exists():
        print(f"[SDRForge] Lab not found: {lab.file}")
        return 1

    env = os.environ.copy()

    env["SDRFORGE_ROOT"] = str(PROJECT_ROOT)
    env["SDRFORGE_IMAGES"] = str(IMAGES_DIR)
    env["SDRFORGE_LABS"] = str(LABS_DIR)

    return subprocess.call(
        [sys.executable, str(lab.file)],
        env=env,
    )


def main() -> None:
    while True:
        labs = discover_labs()

        if not labs:
            print(f"[SDRForge] No labs found in: {LABS_DIR}")
            sys.exit(0)

        selected = run_menu(labs)

        if selected is None:
            break

        launch_lab(selected)

    sys.exit(0)


if __name__ == "__main__":
    main()