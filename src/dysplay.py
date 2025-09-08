import os
import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from dotenv import load_dotenv  # type: ignore


# Ensure we can import sibling module 'aprox.py' when running this file directly
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# Load .env from project root (parent of this file's directory)
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

import aprox  # type: ignore


REFRESH_SECONDS_DEFAULT = 120


def fetch_route_lines(departure_time: int) -> tuple[str, str]:
    """Fetch two routes using aprox helpers and return formatted LED lines.

    Returns two strings like "ROUTE 1  27.0 km  |  21 mins".
    """
    api_key = aprox.load_api_key()

    routes = aprox.load_routes()

    lines: list[str] = []
    for name, lat1, lng1, lat2, lng2 in routes:
        data = aprox.get_route(lat1, lng1, lat2, lng2, api_key, departure_time)
        _distance, duration, _arrival = aprox.parse_route(data, departure_time)
        line = f"{name}  SJ --> Cag  |  {duration}"
        lines.append(line.upper())

    return lines[0], lines[1]


class LedDisplayApp:
    """Tkinter app emulating a highway LED display with two lines."""

    def __init__(self, root: tk.Tk, departure_time: int) -> None:
        self.root = root
        self.root.title("Highway LED Display")
        self.root.configure(bg="#000000")
        self.departure_time = departure_time

        # Allow environment override for refresh seconds
        refresh_env = os.getenv("DISPLAY_REFRESH_SECONDS")
        try:
            self.refresh_seconds = int(refresh_env) if refresh_env else REFRESH_SECONDS_DEFAULT
        except ValueError:
            self.refresh_seconds = REFRESH_SECONDS_DEFAULT

        # Fonts and colors resembling amber LED on black background
        self.led_color = "#FFB000"  # amber
        self.bg_color = "#000000"
        self.font_large = tkfont.Font(family="Courier", size=44, weight="bold")

        # Layout two lines, centered
        self.line1 = tk.Label(
            self.root,
            text="",
            font=self.font_large,
            fg=self.led_color,
            bg=self.bg_color,
            anchor="center",
        )
        self.line1.pack(fill="both", expand=True, padx=24, pady=(36, 12))

        self.line2 = tk.Label(
            self.root,
            text="",
            font=self.font_large,
            fg=self.led_color,
            bg=self.bg_color,
            anchor="center",
        )
        self.line2.pack(fill="both", expand=True, padx=24, pady=(12, 36))

        # Status line for subtle diagnostics (dimmed)
        self.status_font = tkfont.Font(family="Courier", size=12)
        self.status = tk.Label(
            self.root,
            text="",
            font=self.status_font,
            fg="#888888",
            bg=self.bg_color,
            anchor="e",
        )
        self.status.pack(fill="x", padx=16, pady=(0, 12))

        # Initial update and schedule periodic refresh
        self.update_lines()

    def update_lines(self) -> None:
        """Fetch latest values and update the two LED lines."""
        try:
            line1, line2 = fetch_route_lines(self.departure_time)
            self.line1.config(text=line1)
            self.line2.config(text=line2)
            depart_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.departure_time))
            refreshed_str = time.strftime("%Y-%m-%d %H:%M:%S")
            self.status.config(text=f"DEPARTURE: {depart_str}  |  REFRESHED: {refreshed_str}")
        except Exception as exc:  # Broad to ensure display keeps running
            self.line1.config(text="ERROR FETCHING ROUTES")
            self.line2.config(text=str(exc)[:80].upper())
            depart_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.departure_time))
            self.status.config(text=f"DEPARTURE: {depart_str}  |  REFRESHED: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Schedule next refresh
        self.root.after(self.refresh_seconds * 1000, self.update_lines)


def prompt_unix_timestamp() -> int:
    """Prompt the user for a Unix timestamp (seconds). Defaults to now if blank/invalid."""
    print("Enter Unix departure timestamp (seconds). Leave blank for 'now'.")
    user_input = input("> ").strip()
    if user_input == "":
        return int(time.time())
    try:
        return int(user_input)
    except ValueError:
        print("Invalid timestamp. Using current time.")
        return int(time.time())


def main() -> None:
    departure_time = prompt_unix_timestamp()
    root = tk.Tk()
    # Sensible default window size; adjust or make fullscreen as needed
    root.geometry("1000x300")
    app = LedDisplayApp(root, departure_time)
    root.mainloop()


if __name__ == "__main__":
    main()
