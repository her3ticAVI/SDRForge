#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import inspect
import textwrap
import importlib.util
import re

from pathlib import Path
from dataclasses import dataclass
from typing import List

from blessed import Terminal


THIS_FILE = Path(__file__).resolve()
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def clean_len(s: str) -> int:
    return len(ANSI_RE.sub("", s))


def find_project_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        labs_dir = path / "framework" / "labs"
        if labs_dir.exists() and labs_dir.is_dir():
            return path

    print("[SDRForge] Could not find project root.")
    sys.exit(1)


PROJECT_ROOT = find_project_root(THIS_FILE.parent)
LABS_DIR = PROJECT_ROOT / "framework" / "labs"


@dataclass(frozen=True)
class LabInfo:
    name: str
    desc: str
    file: Path
    function: object


ascii_art = """
                                ▪  ▪  ▪
                                  ▪█▪
                             ▄█▄   █   ▄█▄
                           ▄█▀     █     ▀█▄
                          ██    ▄█████▄    ██
                          ██   █████████   ██
                          ██    ▀█████▀    ██
                           ▀█▄     █     ▄█▀
                             ▀█▄   █   ▄█▀
                                  ▄█▄
                                  ███
                                  ███
                                 █████

              ███████╗██████╗ ██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
              ██╔════╝██╔══██╗██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
              ███████╗██║  ██║██████╔╝█████╗  ██║   ██║██████╔╝██║  ███╗█████╗
              ╚════██║██║  ██║██╔══██╗██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
              ███████║██████╔╝██║  ██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
              ╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
"""


def import_module_and_get_function(file_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if not spec or not spec.loader:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "run") and callable(module.run):
        function = module.run
    elif hasattr(module, "main") and callable(module.main):
        function = module.main
    else:
        functions = {
            name: func
            for name, func in inspect.getmembers(module, inspect.isfunction)
            if not name.startswith("_")
            and name not in (
                "find_gnuradio_companion",
                "run_python_flowgraph",
                "open_grc_file",
            )
        }

        if not functions:
            return None

        _, function = next(iter(functions.items()))

    name = getattr(module, "LAB_NAME", file_path.stem.replace("_", " "))
    desc = getattr(module, "LAB_DESC", "No description available.")

    return LabInfo(str(name), str(desc), file_path, function)


def discover_labs() -> List[LabInfo]:
    labs = []

    if not LABS_DIR.exists():
        return labs

    for py in sorted(LABS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue

        if py.name == THIS_FILE.name:
            continue

        lab = import_module_and_get_function(py, py.stem)

        if lab:
            labs.append(lab)

    labs.sort(key=lambda x: x.name.lower())
    return labs


def draw_box(
    term: Terminal,
    top: int,
    left: int,
    width: int,
    height: int,
    title: str,
) -> None:
    title_text = f" {title} "
    side = max((width - 2 - len(title_text)) // 2, 0)

    print(
        term.move(top, left)
        + "┌"
        + "─" * side
        + title_text
        + "─" * (width - 2 - side - len(title_text))
        + "┐"
    )

    for i in range(height):
        print(
            term.move(top + 1 + i, left)
            + "│"
            + " " * (width - 2)
            + "│"
        )

    print(
        term.move(top + height + 1, left)
        + "└"
        + "─" * (width - 2)
        + "┘"
    )


def print_logo(
    term: Terminal,
    top: int,
    art: str,
    center_left: int,
    center_width: int,
) -> int:
    lines = art.strip("\n").splitlines()
    logo_width = max(clean_len(line) for line in lines)

    logo_left = center_left + max((center_width - logo_width) // 2, 0)

    for i, line in enumerate(lines):
        print(term.move(top + i, logo_left) + line)
    by_row = top + len(lines)
    by_left = logo_left + 14
    print(term.move(by_row, by_left) + term.red("By BHIS"))

    return by_row + 1


def draw_outer_box(
    term: Terminal,
    top: int,
    left: int,
    width: int,
    height: int,
    version: str = "Version 0.1.0",
) -> None:
    label = f"|{version}|"
    top_line = "┌" + label + "─" * (width - len(label) - 2) + "┐"

    print(term.move(top, left) + top_line)

    for i in range(height):
        print(
            term.move(top + 1 + i, left)
            + "│"
            + " " * (width - 2)
            + "│"
        )

    print(
        term.move(top + height + 1, left)
        + "└"
        + "─" * (width - 2)
        + "┘"
    )


def print_menu(
    term: Terminal,
    labs: List[LabInfo],
    selected_index: int,
) -> None:
    with term.hidden_cursor():
        print(term.clear)

        lab_width = 33
        desc_width = 55
        box_height = 10
        gap = 4

        inner_width = lab_width + gap + desc_width
        outer_width = inner_width + 4

        outer_left = max((term.width - outer_width) // 2, 0)
        inner_left = outer_left + 2

        logo_bottom = print_logo(
            term=term,
            top=1,
            art=ascii_art,
            center_left=outer_left,
            center_width=outer_width,
        )

        outer_top = logo_bottom + 2
        outer_height = box_height + 2

        draw_outer_box(
            term,
            outer_top,
            outer_left,
            outer_width,
            outer_height,
        )

        lab_left = inner_left
        desc_left = lab_left + lab_width + gap

        box_top = outer_top + 1

        draw_box(term, box_top, lab_left, lab_width, box_height, "Labs")
        draw_box(term, box_top, desc_left, desc_width, box_height, "Description")

        current_lab = labs[selected_index]

        start = max(selected_index - box_height + 1, 0)
        visible_labs = labs[start:start + box_height]

        for idx, lab in enumerate(visible_labs):
            real_index = start + idx
            name = lab.name[: lab_width - 4]

            if real_index == selected_index:
                rendered = term.red(name)
            else:
                rendered = name

            print(term.move(box_top + 1 + idx, lab_left + 2) + rendered)

        wrapped = textwrap.wrap(current_lab.desc, width=desc_width - 5)

        for i, line in enumerate(wrapped[:box_height]):
            print(term.move(box_top + 1 + i, desc_left + 2) + line)

        footer = "[ENTER] Launch    [Q] Quit"
        footer_left = outer_left + max((outer_width - len(footer)) // 2, 0)

        print(
            term.move(outer_top + outer_height + 3, footer_left)
            + term.red(footer)
        )


def launch_lab(lab: LabInfo) -> None:
    os.system("clear")

    try:
        lab.function()

    except Exception as e:
        os.system("clear")
        print("\n[SDRForge] Error launching lab:\n")
        print(e)
        input("\nPress ENTER to return...")


def main() -> None:
    labs = discover_labs()

    if not labs:
        print("[SDRForge] No labs found.")
        sys.exit(1)

    term = Terminal()
    current_row = 0

    with term.cbreak(), term.fullscreen():
        while True:
            print_menu(term, labs, current_row)

            key = term.inkey()

            if key.code == term.KEY_UP and current_row > 0:
                current_row -= 1

            elif key.code == term.KEY_DOWN and current_row < len(labs) - 1:
                current_row += 1

            elif key.code in (term.KEY_ENTER, "\n", "\r"):
                launch_lab(labs[current_row])

            elif key.lower() == "q":
                os.system("clear")
                return


if __name__ == "__main__":
    main()