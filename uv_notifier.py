"""
UV Index Notifier
Checks the current UV index every 30 minutes and notifies you when it goes above a threshold.

Setup:
    pip install requests plyer

Run:
    python uv_notifier.py
"""

import time
from datetime import datetime

import requests

# ---------- Settings (change these) ----------
LATITUDE = 36.62          # Fethiye. Change for another city.
LONGITUDE = 29.11
UV_THRESHOLD = 3          # notify when UV is above this
CHECK_EVERY_MINUTES = 30  # how often to check
REMIND_EVERY_HOURS = 2    # sunscreen reapply reminder while UV stays high
NTFY_TOPIC = ""           # optional: phone notifications, e.g. "my-uv-alerts-8391"
# ---------------------------------------------

API_URL = "https://api.open-meteo.com/v1/forecast"


def get_uv_index():
    """Fetch the current UV index. Returns a float, or None if the request fails."""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "uv_index",
        "timezone": "auto",
    }
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()["current"]["uv_index"]
    except (requests.RequestException, KeyError, ValueError) as error:
        print(f"[{datetime.now():%H:%M}] Could not get UV index: {error}")
        return None


def notify(title, message):
    """Send a desktop notification, and a phone notification if NTFY_TOPIC is set."""
    print(f"[{datetime.now():%H:%M}] {title}: {message}")

    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=10)
    except Exception as error:
        print(f"Desktop notification failed: {error}")

    if NTFY_TOPIC:
        try:
            requests.post(
                f"https://ntfy.sh/{NTFY_TOPIC}",
                data=message.encode("utf-8"),
                headers={"Title": title},
                timeout=10,
            )
        except requests.RequestException as error:
            print(f"Phone notification failed: {error}")


def main():
    print(f"Watching UV index. Will alert when it is above {UV_THRESHOLD}.")
    was_high = False
    last_alert_time = 0.0

    while True:
        uv = get_uv_index()

        if uv is not None:
            print(f"[{datetime.now():%H:%M}] UV index: {uv}")
            is_high = uv > UV_THRESHOLD
            now = time.time()

            if is_high and not was_high:
                notify("UV is high", f"UV index is {uv}. Time to put on sunscreen!")
                last_alert_time = now
            elif is_high and now - last_alert_time >= REMIND_EVERY_HOURS * 3600:
                notify("Reapply sunscreen", f"UV index is still {uv}. Reapply sunscreen.")
                last_alert_time = now
            elif not is_high and was_high:
                print("UV dropped back to a low level.")

            was_high = is_high

        time.sleep(CHECK_EVERY_MINUTES * 60)


if __name__ == "__main__":
    main()
