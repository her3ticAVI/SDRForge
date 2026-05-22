#!/usr/bin/env python3
from __future__ import annotations

import os
import signal
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template
from waitress import serve

from opensky_source import OpenSkySource


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))

source = OpenSkySource()

latest_data = {
    "mode": "Connecting...",
    "timestamp": time.time(),
    "aircraft": []
}

last_browser_heartbeat = time.time()
browser_connected = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/aircraft")
def api_aircraft():
    return jsonify(latest_data)


@app.route("/api/heartbeat", methods=["POST"])
def api_heartbeat():
    global last_browser_heartbeat, browser_connected

    last_browser_heartbeat = time.time()
    browser_connected = True

    return jsonify({"ok": True})


def shutdown_server():
    print("[*] Browser closed. Returning to SDRForge menu...")
    os.kill(os.getpid(), signal.SIGINT)


def aircraft_loop():
    global latest_data

    while True:
        aircraft = source.read_aircraft()

        if aircraft:
            latest_data = {
                "mode": "REAL AIRCRAFT DATA - SOFTWARE ONLY",
                "timestamp": time.time(),
                "aircraft": aircraft,
            }
        else:
            latest_data["mode"] = "OpenSky returned no data - showing last good data"

        time.sleep(60)


def browser_watchdog():
    global browser_connected

    while True:
        time.sleep(1)

        if browser_connected:
            seconds_since_heartbeat = time.time() - last_browser_heartbeat

            if seconds_since_heartbeat > 3:
                shutdown_server()


def open_browser():
    time.sleep(1)

    try:
        webbrowser.open("http://127.0.0.1:5055")
    except Exception:
        pass


def main():
    print()
    print("======================================")
    print(" SDRForge ADS-B Aircraft Tracker")
    print("======================================")
    print()
    print("[*] Secure local server starting...")
    print("[*] URL: http://127.0.0.1:5055")
    print("[*] Bound to localhost only")
    print("[*] Source: OpenSky Network")
    print("[*] Mode: Software-only")
    print("[*] Close browser tab to return to SDRForge menu")
    print("[*] Refreshing the browser will NOT close the lab")
    print("[*] Press CTRL+C to stop")
    print()

    threading.Thread(target=aircraft_loop, daemon=True).start()
    threading.Thread(target=browser_watchdog, daemon=True).start()
    threading.Thread(target=open_browser, daemon=True).start()

    serve(
        app,
        host="127.0.0.1",
        port=5055,
        threads=8
    )


if __name__ == "__main__":
    main()