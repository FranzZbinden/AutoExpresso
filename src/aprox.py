import requests  # type: ignore
import os
import time
from datetime import datetime

# Load API key from file 'api' in the same directory
API_KEY_FILE = os.path.join(os.path.dirname(__file__), 'api')
with open(API_KEY_FILE) as f:
    API_KEY = f.read().strip()

def main():
    coords_a = input("18.269514 -66.039249")
    lat1, lng1 = map(float, coords_a.split())
    coords_b = input("18.336549 -66.063951")
    lat2, lng2 = map(float, coords_b.split())
    departure_time = int(time.time())
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': f"{lat1},{lng1}",
        'destination': f"{lat2},{lng2}",
        'mode': 'driving',
        'departure_time': departure_time,
        'key': API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data.get('status') == 'OK' and data.get('routes'):
        leg = data['routes'][0]['legs'][0]
        print(f"Distance: {leg['distance']['text']}")
        print(f"Estimated travel time: {leg['duration']['text']}")
        arrival = leg.get('arrival_time', {}).get('text')
        if arrival:
            print(f"Estimated arrival time: {arrival}")
    else:
        print("Error:", data.get('status'), data.get('error_message', ''))

if __name__ == "__main__":
    main()
