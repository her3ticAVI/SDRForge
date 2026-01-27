#!/usr/bin/env python3
"""
Layout:
- Left: Labs
- Right: Main area split into:
    - Logo panel (bordered) with PNG
    - Doorbell panel (bordered) with ASCII animation
- Bottom: compact dashboard/status strip
- g: opens Wave Viewer screen (SIM waveform)

Main keys:
  q  quit
  d  toggle animation
  g  open wave viewer
"""

# Dependency check (Textual + textual-image)
import sys
import subprocess
import importlib.util
from pathlib import Path


def _pip_install(*pkgs: str) -> None:
    """
    Install pkgs using pip.
    On Kali/Debian, prefer --break-system-packages.
    """
    cmd = [sys.executable, "-m", "pip", "install", "--break-system-packages", *pkgs]
    try:
        subprocess.check_call(cmd)
        return
    except Exception:
        cmd2 = [sys.executable, "-m", "pip", "install", *pkgs]
        try:
            subprocess.check_call(cmd2)
        except Exception as e:
            print("\n[SDRForge] pip install failed.")
            print("Try:")
            print(f"  {sys.executable} -m pip install --break-system-packages {' '.join(pkgs)}")
            raise SystemExit(1) from e


def ensure_deps() -> None:
    if importlib.util.find_spec("textual") is None:
        print("[SDRForge] 'textual' not found. Installing...")
        _pip_install("textual")

    if importlib.util.find_spec("textual_image") is None:
        print("[SDRForge] 'textual-image' not found. Installing...")
        _pip_install("textual-image")


ensure_deps()
LOGO_ORIG = Path("images/SDRLogoDark.png")
LOGO_CACHE = Path("images/.sdrforge_logo_small.png")
ENABLE_LOGO_RESIZE = True

def ensure_small_logo() -> str:
    """
    Generate a smaller logo image for terminal rendering.
    This reduces 'blockiness' because fewer pixels must map to character cells.

    If Pillow isn't installed, we fall back to the original.
    """
    if not ENABLE_LOGO_RESIZE:
        return str(LOGO_ORIG)

    #if cache exists and is newer than original, use it.
    try:
        if LOGO_CACHE.exists() and LOGO_CACHE.stat().st_mtime >= LOGO_ORIG.stat().st_mtime:
            return str(LOGO_CACHE)
    except Exception:
        return str(LOGO_ORIG)

    try:
        from PIL import Image as PILImage  # type: ignore
    except Exception:
        # No pillow -> can't resize; use original
        return str(LOGO_ORIG)

    try:
        if not LOGO_ORIG.exists():
            return str(LOGO_ORIG)

        img = PILImage.open(LOGO_ORIG).convert("RGBA")
        target_w = 460
        w, h = img.size
        if w > target_w:
            target_h = int(h * (target_w / w))
            img = img.resize((target_w, target_h), resample=PILImage.LANCZOS)

        LOGO_CACHE.parent.mkdir(parents=True, exist_ok=True)
        img.save(LOGO_CACHE)
        return str(LOGO_CACHE)
    except Exception:
        return str(LOGO_ORIG)


LOGO_PATH = ensure_small_logo()

# imports after deps
import math
from dataclasses import dataclass
from typing import List

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive

from textual_image.widget import Image


# ASCII ART (animation)
DOORBELL_ART = r"""
  .----.
 / .--. \
| | () | |
|  `--'  |
 \      /
  `----'
"""

LAPTOP_ART = r"""
   _____________
  |  _________  |
  | |         | |
  | |         | |
  | |_________| |
  |_____________|
   \___________/
"""

HOUSE_ART = r"""
      /\
     /  \
    /____\
    | __ |
    ||  ||
    ||__||
    |____|
"""


def build_scene(signal_index: int, stage: int, term_w: int = 80) -> str:
    """Build one frame of the doorbell->laptop->house ASCII animation, centered to term_w."""
    left_pad = 2
    col_width = 24
    bell_col = 0 * col_width + left_pad
    laptop_col = 1 * col_width + left_pad
    house_col = 2 * col_width + left_pad

    bell = DOORBELL_ART.strip("\n").splitlines()
    laptop = LAPTOP_ART.strip("\n").splitlines()
    house = HOUSE_ART.strip("\n").splitlines()

    art_h = max(len(bell), len(laptop), len(house))
    scene_w = house_col + 22
    term_w = max(term_w, scene_w + 4)

    pad_left = max(0, (term_w - scene_w) // 2)
    width = pad_left + scene_w

    canvas: List[str] = []
    for i in range(art_h):
        line = [" "] * width
        if i < len(bell):
            seg = bell[i]
            line[pad_left + bell_col : pad_left + bell_col + len(seg)] = seg
        if i < len(laptop):
            seg = laptop[i]
            line[pad_left + laptop_col : pad_left + laptop_col + len(seg)] = seg
        if i < len(house):
            seg = house[i]
            line[pad_left + house_col : pad_left + house_col + len(seg)] = seg
        canvas.append("".join(line))

    path_y = art_h + 2
    while len(canvas) <= path_y + 3:
        canvas.append(" " * width)

    # path
    base = list(canvas[path_y])
    for x in range(pad_left + bell_col + 10, pad_left + house_col + 8):
        if 0 <= x < width:
            base[x] = "-"
    canvas[path_y] = "".join(base)

    # labels
    labels_y = path_y + 2
    for label, col in [("[Doorbell]", bell_col), ("[Laptop]", laptop_col), ("[House]", house_col)]:
        row = list(canvas[labels_y])
        for i, ch in enumerate(label):
            xx = pad_left + col + i
            if 0 <= xx < len(row):
                row[xx] = ch
        canvas[labels_y] = "".join(row)

    # signal
    sig_y = path_y - 1
    if stage == 0:
        start_x = pad_left + bell_col + 10
        end_x = pad_left + laptop_col - 2
    else:
        start_x = pad_left + laptop_col + 8
        end_x = pad_left + house_col - 2

    span = max(1, end_x - start_x)
    x = start_x + max(0, min(signal_index, span))
    row = list(canvas[sig_y])
    for i, ch in enumerate(")))"):
        xx = x + i
        if 0 <= xx < width:
            row[xx] = ch
    canvas[sig_y] = "".join(row)

    return "\n".join(canvas)


# Wave render helpers
def samples_to_sparkline(samples: List[float], width: int) -> str:
    if not samples:
        return "(no samples)"
    width = max(10, width)
    step = max(1, len(samples) // width)
    pts = [samples[i] for i in range(0, len(samples), step)][:width]
    peak = max(1e-9, max(abs(x) for x in pts))
    blocks = " ▁▂▃▄▅▆▇█"
    out = []
    for x in pts:
        level = int(round((abs(x) / peak) * 8))
        level = max(0, min(8, level))
        out.append(blocks[level])
    return "".join(out)


def bits_from_samples(samples: List[float], chunk: int = 240, thresh: float = 0.18) -> str:
    if not samples:
        return ""
    bits = []
    for i in range(0, len(samples), chunk):
        seg = samples[i : i + chunk]
        if not seg:
            break
        avg = sum(abs(x) for x in seg) / len(seg)
        bits.append("1" if avg >= thresh else "0")
    return "".join(bits)


@dataclass
class SimSignal:
    sr: int
    samples: List[float]
    label: str


def gen_sim_signal(scenario: int, seconds: float = 1.25, sr: int = 48000) -> SimSignal:
    n = int(seconds * sr)
    out: List[float] = [0.0] * n

    def env_decay(t: float, k: float) -> float:
        return math.exp(-k * t)

    if scenario == 1:
        label = "Scenario 1: pulse train"
        for i in range(n):
            t = i / sr
            burst = 1.0 if (t % 0.22) < 0.06 else 0.0
            out[i] = 0.8 * burst * math.sin(2 * math.pi * 880 * t)

    elif scenario == 2:
        label = "Scenario 2: FSK-ish"
        bit_rate = 120
        f0, f1 = 900, 1400
        for i in range(n):
            t = i / sr
            bit_i = int(t * bit_rate)
            b = 1 if (bit_i % 3) else 0
            f = f1 if b else f0
            out[i] = 0.75 * math.sin(2 * math.pi * f * t)

    else:
        label = "Scenario 3: doorbell burst"
        for i in range(n):
            t = i / sr
            if t > 0.85:
                out[i] = 0.0
                continue
            f = 500 + (1500 * min(1.0, t / 0.35))
            out[i] = 0.95 * env_decay(t, 3.2) * math.sin(2 * math.pi * f * t)

    return SimSignal(sr=sr, samples=out, label=label)


class WaveViewerScreen(Screen):
    scenario = reactive(3)
    paused = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="wave_top")
        yield Static("", id="wave_bottom")
        yield Footer()

    def on_mount(self) -> None:
        self._regenerate()
        self.set_interval(0.15, self._tick)

    def _regenerate(self) -> None:
        self._sig = gen_sim_signal(self.scenario)
        self._cursor = 0

    def _tick(self) -> None:
        top = self.query_one("#wave_top", Static)
        bot = self.query_one("#wave_bottom", Static)

        if not self.paused:
            self._cursor += int(self._sig.sr * 0.03)
            if self._cursor >= len(self._sig.samples):
                self._cursor = 0

        w = max(60, self.size.width - 6)
        window = int(self._sig.sr * 0.18)
        start = self._cursor
        end = min(len(self._sig.samples), start + window)
        seg = self._sig.samples[start:end]

        wave = samples_to_sparkline(seg, width=min(w, 180))
        bits = bits_from_samples(self._sig.samples, chunk=240, thresh=0.18)
        bits_tail = bits[-256:] if bits else ""

        top.update(
            "[b]Wave Viewer (SIM)[/b]\n"
            "────────────────────\n"
            f"{self._sig.label}\n"
            f"Sample rate: {self._sig.sr} Hz   •   paused: {self.paused}\n"
            f"{wave}\n"
        )

        bot.update(
            "[b]Derived 01s[/b] (amp threshold, tail)\n"
            f"{bits_tail}\n"
            "[b]Keys:[/b]  1/2/3 scenario   space pause   r regen   b/esc back\n"
        )

    def on_key(self, event) -> None:
        k = event.key
        if k in ("escape", "b"):
            event.prevent_default()
            event.stop()
            self.app.pop_screen()
            return
        if k == "space":
            event.prevent_default()
            event.stop()
            self.paused = not self.paused
            return
        if k == "r":
            event.prevent_default()
            event.stop()
            self._regenerate()
            return
        if k in ("1", "2", "3"):
            event.prevent_default()
            event.stop()
            self.scenario = int(k)
            self._regenerate()
            return


class SDRForgeApp(App):
    TITLE = "SDRForge"
    SUB_TITLE = "TUI Signal Lab (SIM)"

    CSS = """
    Screen { layout: vertical; padding: 0; }
    #top-row { height: 1fr; }

    /* Left labs */
    #menu-panel {
        width: 34;
        height: 100%;
        border: round #666666;
        padding: 0 1;
    }

    /* Main right container */
    #main-panel {
        width: 1fr;
        height: 100%;
        border: round #666666;
        padding: 0 1;
    }

    /* Separate boxed logo panel */
    #logo-panel {
        height: 14;
        border: round #666666;
        padding: 0 1;
        content-align: center middle;
    }

    /* Image fills logo-panel */
    #main-logo {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }

    /* Separate boxed animation panel */
    #anim-panel {
        height: 1fr;
        border: round #666666;
        padding: 0 1;
        content-align: center middle;
    }

    #dashboard-panel {
        height: 9;
        border: round #666666;
        padding: 0 1;
    }
    #wave_top { height: 1fr; border: round #666666; padding: 0 1; }
    #wave_bottom { height: 9; border: round #666666; padding: 0 1; }
    """

    BINDINGS = [
        ("q", "quit_app", "Quit"),
        ("d", "toggle_doorbell", "Toggle Doorbell"),
        ("g", "open_wave", "Wave Viewer"),
    ]

    _anim_idx = 0
    _anim_stage = 0
    _anim_running = True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="top-row"):
            with Vertical(id="menu-panel"):
                yield Static(
                    "[b]Labs[/b]\n"
                    " 2.) Car Hacking\n"
                    " 3.) Satellite Hacking\n"
                    " 4.) TBD\n"
                    " 5.) TBD\n"
                )

            with Vertical(id="main-panel"):
                with Vertical(id="logo-panel"):
                    yield Image(LOGO_PATH, id="main-logo")
                yield Static("", id="anim-panel")

        yield Static("", id="dashboard-panel")
        yield Footer()

    def on_mount(self) -> None:
        self._set_status("Ready.")
        self.set_interval(0.04, self._tick_doorbell)

    def _set_status(self, msg: str) -> None:
        dash = self.query_one("#dashboard-panel", Static)
        dash.update(
            "[b]Dashboard[/b]  "
            f"[dim]Status:[/dim] [b]{msg}[/b]\n"
            "[dim]d[/dim]=toggle  [dim]g[/dim]=wave  [dim]q[/dim]=quit"
        )

    def _tick_doorbell(self) -> None:
        if not self._anim_running:
            return

        self._anim_idx += 1
        if self._anim_idx >= 30:
            self._anim_idx = 0
            self._anim_stage = 1 - self._anim_stage

        panel = self.query_one("#anim-panel", Static)
        panel_width = panel.size.width or self.size.width
        usable_w = max(20, panel_width - 4)
        panel.update(build_scene(self._anim_idx, self._anim_stage, term_w=usable_w))

    def action_quit_app(self) -> None:
        self.exit()

    def action_toggle_doorbell(self) -> None:
        self._anim_running = not self._anim_running
        if not self._anim_running:
            self.query_one("#anim-panel", Static).update("[dim](animation paused)[/dim]")
            self._set_status("Animation paused.")
        else:
            self._set_status("Animation running.")

    def action_open_wave(self) -> None:
        self.push_screen(WaveViewerScreen())
        self._set_status("Wave Viewer open.")


if __name__ == "__main__":
    SDRForgeApp().run()