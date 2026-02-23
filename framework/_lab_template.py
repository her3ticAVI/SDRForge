#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


# --------- REQUIRED METADATA (used by SDRForge menu if you add parsing later) ---------
# SDRFORGE_DESC: (one sentence) What this lab teaches.
# SDRFORGE_TOPICS: comma, separated, topics, here


# --------- STANDARDIZED OUTPUT HELPERS ---------
def _hr(char: str = "=", n: int = 56) -> str:
    return char * n


def _banner(title: str, subtitle: Optional[str] = None) -> None:
    print("\n" + _hr("="))
    print(title)
    if subtitle:
        print(subtitle)
    print(_hr("=") + "\n")


def _section(title: str) -> None:
    print(_hr("-"))
    print(title)
    print(_hr("-"))


def _bullet(lines: List[str]) -> None:
    for line in lines:
        print(f"• {line}")
    print("")


def _keyvals(pairs: List[Tuple[str, str]]) -> None:
    w = max((len(k) for k, _ in pairs), default=0)
    for k, v in pairs:
        print(f"{k:<{w}} : {v}")
    print("")


def _tutor(msg: str) -> None:
    if os.environ.get("SDRFORGE_TUTOR", "").strip() in {"1", "true", "True", "yes", "YES"}:
        print(f"[LEARN] {msg}\n")


def _pause(msg: str = "Press Enter to continue...") -> None:
    try:
        input(msg)
    except EOFError:
        pass


# --------- STANDARD LAB MODELS ---------
@dataclass(frozen=True)
class LabPaths:
    root: Path
    images: Path
    labs: Path
    out: Path


@dataclass(frozen=True)
class LabContext:
    paths: LabPaths
    started_at: float
    args: argparse.Namespace


# --------- CORE TEMPLATE HOOKS (YOU FILL THESE IN) ---------
def lab_info() -> Dict[str, object]:
    """
    REQUIRED: Return a stable info block so every lab looks the same.
    """
    return {
        "title": "LAB TITLE HERE",
        "subtitle": "Short subtitle (what you are doing)",
        "objectives": [
            "Objective 1",
            "Objective 2",
            "Objective 3",
        ],
        "prereqs": [
            "Required: RTL-SDR plugged in",
            "Optional: SDRFORGE_TUTOR=1 for extra learning notes",
        ],
        "ethics": [
            "Only capture signals you own/control and have permission to analyze.",
        ],
        "topics": [
            "center frequency",
            "sample rate",
            "IQ samples",
        ],
    }


def define_cli(parser: argparse.ArgumentParser) -> None:
    """
    OPTIONAL: Add CLI args in a consistent way for all labs.
    """
    # Example common args:
    parser.add_argument("--out", default="captures", help="Output directory")
    parser.add_argument("--label", default="capture", help="Label prefix for output files")
    # Add your lab-specific args below:
    # parser.add_argument("--freq", type=float, default=433.92e6, help="Center frequency (Hz)")
    # parser.add_argument("--sr", type=float, default=2.0e6, help="Sample rate (S/s)")
    # parser.add_argument("--dur", type=float, default=3.0, help="Duration (s)")


def quiz_questions(ctx: LabContext) -> List[Tuple[str, List[str], str, str]]:
    """
    OPTIONAL: Return quiz questions in the standardized format:
      (question, [options], correct_letter, explanation)
    Return [] to skip quiz.
    """
    return [
        # ("Question?", ["A) ...", "B) ...", "C) ...", "D) ..."], "B", "Explanation...")
    ]


def lab_run(ctx: LabContext) -> int:
    """
    REQUIRED: Your lab logic goes here.
    Return 0 for success, non-zero for failure.
    """
    _section("Lab Work")
    print("YOUR LAB CODE HERE (capture/analyze/save/etc.)\n")

    # Example:
    # paths = ctx.paths
    # out_file = paths.out / f"{ctx.args.label}_{int(time.time())}.bin"
    # out_file.write_bytes(b"example")
    # print(f"Saved: {out_file}")

    return 0


def lab_exercises(ctx: LabContext) -> List[str]:
    """
    OPTIONAL: End-of-lab exercises/questions to reinforce learning.
    """
    return [
        "Exercise 1: Change one parameter and observe the effect.",
        "Exercise 2: Repeat capture 5 times and compare burst lengths.",
    ]


# --------- TEMPLATE IMPLEMENTATION (DON'T TOUCH MUCH) ---------
def _resolve_paths(out_dir: str) -> LabPaths:
    root = Path(os.environ.get("SDRFORGE_ROOT", Path(__file__).resolve().parents[2])).resolve()
    images = Path(os.environ.get("SDRFORGE_IMAGES", root / "images")).resolve()
    labs = Path(os.environ.get("SDRFORGE_LABS", root / "framework" / "labs")).resolve()
    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    return LabPaths(root=root, images=images, labs=labs, out=out)


def _run_quiz(qs: List[Tuple[str, List[str], str, str]]) -> None:
    if not qs:
        return
    _section("Waveform Quiz")
    score = 0
    for q, options, ans, explain in qs:
        print(q)
        for opt in options:
            print("   " + opt)
        user = input("\nYour answer (A/B/C/D): ").strip().upper()
        if user == ans.strip().upper():
            print("✔ Correct")
            score += 1
        else:
            print("✘ Incorrect")
        print(explain)
        print("")
        print(_hr("-", 45))
        print("")
    print(f"Score: {score}/{len(qs)}\n")
    _pause("Press Enter to start the lab...\n")


def main() -> int:
    info = lab_info()
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description=str(info.get("subtitle", "")),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    define_cli(parser)
    args = parser.parse_args()

    paths = _resolve_paths(getattr(args, "out", "captures"))
    ctx = LabContext(paths=paths, started_at=time.time(), args=args)

    _banner(str(info.get("title", "SDRForge Lab")), str(info.get("subtitle", "")))

    _section("Objectives")
    _bullet([str(x) for x in info.get("objectives", [])])

    _section("Prerequisites")
    _bullet([str(x) for x in info.get("prereqs", [])])

    _section("Ethics / Permission")
    _bullet([str(x) for x in info.get("ethics", [])])

    _section("Quick Setup")
    _keyvals([
        ("Output folder", str(paths.out)),
        ("SDRFORGE_ROOT", str(paths.root)),
        ("Tutor mode", "ON" if os.environ.get("SDRFORGE_TUTOR") else "OFF"),
    ])

    _tutor(
        "Reminder: sample rate controls captured bandwidth; IQ is complex baseband. "
        "Short bursts often show up as amplitude spikes and vertical streaks in a waterfall."
    )

    qs = quiz_questions(ctx)
    _run_quiz(qs)

    rc = lab_run(ctx)

    _section("Exercises")
    _bullet(lab_exercises(ctx))

    _section("Result")
    print("Completed" if rc == 0 else f"Failed (code={rc})")
    print("")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
