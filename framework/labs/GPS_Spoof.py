#!/usr/bin/env python3
from __future__ import annotations

import http.server
import socketserver
import threading
import webbrowser
import time

from pathlib import Path
from urllib.parse import urlparse

LAB_NAME = "GPS Spoof"

LAB_DESC = (
    "Software-only GPS spoofing simulator.\n\n"
    "Shows a simulated GPS location on a live map.\n"
    "Uses browser geolocation when available.\n"
    "Includes Scramble, Drift, and Carry-Off modes."
)

PORT = 8765

LAST_HEARTBEAT = time.time()

SERVER_RUNNING = True

socketserver.TCPServer.allow_reuse_address = True


class GPSHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        global LAST_HEARTBEAT

        parsed = urlparse(self.path)

        if parsed.path == "/heartbeat":
            LAST_HEARTBEAT = time.time()

            self.send_response(204)
            self.end_headers()

            return

        try:
            super().do_GET()

        except BrokenPipeError:
            pass

        except ConnectionResetError:
            pass


def start_server(directory: Path):
    global SERVER_RUNNING

    class Handler(GPSHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(
                *args,
                directory=str(directory),
                **kwargs
            )

    with socketserver.TCPServer(
        ("localhost", PORT),
        Handler
    ) as httpd:

        httpd.timeout = 1

        print(f"[+] GPS Spoof server running on port {PORT}")

        while SERVER_RUNNING:
            httpd.handle_request()


def launch():
    global SERVER_RUNNING
    global LAST_HEARTBEAT

    current_file = Path(__file__).resolve()

    framework_dir = current_file.parent.parent

    project_dir = framework_dir.parent

    config_dir = project_dir / "configs" / "GPS_Spoof"

    required_files = [
        "gps_spoof.html",
        "style.css",
        "spoof.js",
    ]

    if not config_dir.exists():
        print(f"[ERROR] Missing config folder:")
        print(config_dir)

        return

    for file in required_files:
        file_path = config_dir / file

        if not file_path.exists():
            print(f"[ERROR] Missing file:")
            print(file_path)

            return

    SERVER_RUNNING = True

    LAST_HEARTBEAT = time.time()

    server_thread = threading.Thread(
        target=start_server,
        args=(config_dir,),
        daemon=True,
    )

    server_thread.start()

    url = f"http://localhost:{PORT}/gps_spoof.html"

    print(f"[+] Launching GPS Spoof:")
    print(url)

    webbrowser.open(url)

    print(
        "\n[+] Close the GPS Spoof browser tab "
        "to return to SDRForge...\n"
    )

    time.sleep(3)

    while True:
        time.sleep(1)

        if time.time() - LAST_HEARTBEAT > 4:
            print(
                "[+] GPS Spoof tab closed. "
                "Returning to SDRForge..."
            )

            SERVER_RUNNING = False

            break


if __name__ == "__main__":
    launch()