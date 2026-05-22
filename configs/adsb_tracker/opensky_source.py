from __future__ import annotations

import time
import requests


class OpenSkySource:

    def __init__(self):

        self.url = "https://opensky-network.org/api/states/all"

        self.headers = {
            "User-Agent": "SDRForge-ADSB/1.0"
        }

    def read_aircraft(self):

        try:

            r = requests.get(
                self.url,
                headers=self.headers,
                timeout=15
            )

            r.raise_for_status()

            data = r.json()

        except Exception as e:

            print(f"[!] OpenSky request failed: {e}")

            return []

        aircraft = []

        for state in data.get("states", []):

            try:

                icao = state[0]

                callsign = (state[1] or "UNKNOWN").strip()

                lon = state[5]
                lat = state[6]

                altitude_m = state[7]
                velocity_ms = state[9]
                heading = state[10]
                vertical_rate_ms = state[11]

                if lat is None or lon is None:
                    continue

                aircraft.append({
                    "icao": str(icao).upper(),
                    "callsign": callsign,
                    "lat": lat,
                    "lon": lon,
                    "altitude": int((altitude_m or 0) * 3.28084),
                    "speed": int((velocity_ms or 0) * 1.94384),
                    "heading": int(heading or 0),
                    "vertical_rate": int((vertical_rate_ms or 0) * 196.85),
                    "last_seen": time.time(),
                })

            except Exception:
                continue

        print(f"[*] Loaded {len(aircraft)} aircraft")

        return aircraft[:200]