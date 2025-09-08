import requests  # type: ignore
import os
import time
from datetime import datetime
from dotenv import load_dotenv  # type: ignore

# Load .env from project root (parent of this file's directory)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def load_api_key() -> str:
    """Read the Google API key from env or fallback to the 'api' file."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if api_key:
        return api_key.strip()
    key_file = os.path.join(os.path.dirname(__file__), 'api')
    with open(key_file) as f:
        return f.read().strip()


def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise EnvironmentError(f"Missing environment variable: {name}")
    return value


def _require_float_env(name: str) -> float:
    value = _require_env(name)
    try:
        return float(value)
    except ValueError:
        raise EnvironmentError(f"Invalid float for {name}: {value!r}")


def _parse_latlng_pair(value: str) -> tuple[float, float]:
    """Parse a combined "lat,lng" (or space-separated) string into floats.

    Accepts formats like "18.27,-66.03" or "18.27 -66.03" with optional spaces.
    """
    cleaned = value.strip()
    # Try comma-separated first
    if "," in cleaned:
        parts = [p.strip() for p in cleaned.split(",")]
    else:
        parts = cleaned.split()
    if len(parts) != 2:
        raise EnvironmentError(f"Invalid coordinate pair: {value!r}. Expected 'lat,lng'.")
    try:
        lat = float(parts[0])
        lng = float(parts[1])
    except ValueError:
        raise EnvironmentError(f"Invalid coordinate numbers in: {value!r}")
    return lat, lng


def _read_coords(prefix: str) -> tuple[float, float]:
    """Read coordinates for a given prefix.

    Prefers combined env var (e.g., ROUTE1_ORIGIN="lat,lng"). If absent,
    falls back to separate vars (e.g., ROUTE1_ORIGIN_LAT / ROUTE1_ORIGIN_LNG).
    """
    combined = os.getenv(prefix)
    if combined is not None and combined.strip() != "":
        return _parse_latlng_pair(combined)
    lat = _require_float_env(f"{prefix}_LAT")
    lng = _require_float_env(f"{prefix}_LNG")
    return lat, lng


def load_routes() -> list[tuple[str, float, float, float, float]]:
    """Load two routes strictly from environment variables.

    Supports either combined pairs (ROUTE*_ORIGIN, ROUTE*_DEST as "lat,lng")
    or separate vars (ROUTE*_ORIGIN_LAT/LNG, ROUTE*_DEST_LAT/LNG).

    Raises EnvironmentError if any required variable is missing/invalid.

    Returns a list of (name, lat1, lng1, lat2, lng2).
    """
    r1_name = _require_env("ROUTE1_NAME")
    r1_lat1, r1_lng1 = _read_coords("ROUTE1_ORIGIN")
    r1_lat2, r1_lng2 = _read_coords("ROUTE1_DEST")

    r2_name = _require_env("ROUTE2_NAME")
    r2_lat1, r2_lng1 = _read_coords("ROUTE2_ORIGIN")
    r2_lat2, r2_lng2 = _read_coords("ROUTE2_DEST")

    return [
        (r1_name, r1_lat1, r1_lng1, r1_lat2, r1_lng2),
        (r2_name, r2_lat1, r2_lng1, r2_lat2, r2_lng2),
    ]

# def get_coords(prompt: str) -> tuple[float, float]:
#     """Prompt for latitude and longitude and return as floats"""
#     coords = input(prompt)
#     lat_str, lng_str = coords.split()
#     return float(lat_str), float(lng_str)

def get_route(lat1: float, lng1: float, lat2: float, lng2: float, api_key: str, departure_time: int) -> dict:
    """Call the Directions API and return the JSON response"""
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': f"{lat1},{lng1}",
        'destination': f"{lat2},{lng2}",
        'mode': 'driving',
        'departure_time': departure_time,
        'traffic_model': os.getenv("TRAFFIC_MODEL", "best_guess"),
        'key': api_key
    }
    response = requests.get(url, params=params)
    return response.json()

def parse_route(data: dict, departure_time: int) -> tuple[str, str, str | None]:
    """Extract distance, traffic-aware duration, and computed arrival time."""
    if data.get('status') == 'OK' and data.get('routes'):
        leg = data['routes'][0]['legs'][0]
        distance = leg['distance']['text']

        duration_obj = leg.get('duration_in_traffic') or leg.get('duration')
        duration_text = duration_obj['text']
        duration_value = int(duration_obj['value'])

        arrival_ts = departure_time + duration_value
        arrival_text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(arrival_ts))
        return distance, duration_text, arrival_text
    else:
        raise ValueError(f"API error: {data.get('status')}: {data.get('error_message', '')}")

def print_route(distance: str, duration: str, arrival: str | None) -> None:
    """Print the routing information to the console"""
    print(f"Distance: {distance}")
    print(f"Estimated travel time: {duration}")
    if arrival:
        print(f"Estimated arrival time: {arrival}")

def main():
    # Load API key
    api_key = load_api_key()
    # Load routes from environment (with defaults)
    routes = load_routes()
    departure_time = int(time.time())
    for name, lat1, lng1, lat2, lng2 in routes:
        print(f"=== {name} ===")
        try:
            data = get_route(lat1, lng1, lat2, lng2, api_key, departure_time)
            distance, duration, arrival = parse_route(data, departure_time)
            print_route(distance, duration, arrival)
        except ValueError as err:
            print(err)

if __name__ == "__main__":
    main()
