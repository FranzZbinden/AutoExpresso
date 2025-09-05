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


def load_routes() -> list[tuple[str, float, float, float, float]]:
    """Load two routes from environment variables, with sane defaults.

    Returns a list of (name, lat1, lng1, lat2, lng2).
    """
    # Defaults mirror previous hard-coded values
    r1_name = os.getenv("ROUTE1_NAME", "Normal")
    r1_lat1 = _get_float_env("ROUTE1_ORIGIN_LAT", 18.411689)
    r1_lng1 = _get_float_env("ROUTE1_ORIGIN_LNG", -66.070034)
    r1_lat2 = _get_float_env("ROUTE1_DEST_LAT", 18.247645)
    r1_lng2 = _get_float_env("ROUTE1_DEST_LNG", -66.012439)

    r2_name = os.getenv("ROUTE2_NAME", "Faster")
    r2_lat1 = _get_float_env("ROUTE2_ORIGIN_LAT", 18.411725)
    r2_lng1 = _get_float_env("ROUTE2_ORIGIN_LNG", -66.070182)
    r2_lat2 = _get_float_env("ROUTE2_DEST_LAT", 18.247645)
    r2_lng2 = _get_float_env("ROUTE2_DEST_LNG", -66.012439)

    return [
        (r1_name, r1_lat1, r1_lng1, r1_lat2, r1_lng2),
        (r2_name, r2_lat1, r2_lng1, r2_lat2, r2_lng2),
    ]

def get_coords(prompt: str) -> tuple[float, float]:
    """Prompt for latitude and longitude and return as floats"""
    coords = input(prompt)
    lat_str, lng_str = coords.split()
    return float(lat_str), float(lng_str)

def get_route(lat1: float, lng1: float, lat2: float, lng2: float, api_key: str, departure_time: int) -> dict:
    """Call the Directions API and return the JSON response"""
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': f"{lat1},{lng1}",
        'destination': f"{lat2},{lng2}",
        'mode': 'driving',
        'departure_time': departure_time,
        'key': api_key
    }
    response = requests.get(url, params=params)
    return response.json()

def parse_route(data: dict) -> tuple[str, str, str | None]:
    """Extract distance, duration, and arrival time from the API response"""
    if data.get('status') == 'OK' and data.get('routes'):
        leg = data['routes'][0]['legs'][0]
        distance = leg['distance']['text']
        duration = leg['duration']['text']
        arrival = leg.get('arrival_time', {}).get('text')
        return distance, duration, arrival
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
            distance, duration, arrival = parse_route(data)
            print_route(distance, duration, arrival)
        except ValueError as err:
            print(err)

if __name__ == "__main__":
    main()
