#!/usr/bin/env python3

from pathlib import Path
import logging
import os
import signal
import threading
import time

from flask import Flask, render_template, request, abort

BASE_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 5055

last_seen = 0

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static",
)

logging.getLogger("werkzeug").disabled = True


@app.after_request
def secure_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    global last_seen

    if request.remote_addr != "127.0.0.1":
        abort(403)

    last_seen = time.time()
    return "", 204


def browser_watchdog():
    global last_seen

    print("[+] Waiting for browser heartbeat...")

    while last_seen == 0:
        time.sleep(1)

    print("[+] Browser heartbeat detected.")

    misses = 0

    while True:
        time.sleep(1)

        if time.time() - last_seen > 2:
            misses += 1
        else:
            misses = 0

        if misses >= 3:
            print("[+] Browser closed. Returning to SDRForge menu...")
            os.kill(os.getpid(), signal.SIGTERM)


if __name__ == "__main__":
    threading.Thread(target=browser_watchdog, daemon=True).start()

    try:
        from waitress import serve
        print(f"[+] IMSI Catcher running securely on http://{HOST}:{PORT}")
        serve(app, host=HOST, port=PORT)
    except ImportError:
        app.run(host=HOST, port=PORT, debug=False, use_reloader=False)