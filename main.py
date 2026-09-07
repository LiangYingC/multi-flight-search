import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

"""
How to use it:
1. Get a free API key from https://serpapi.com/manage-api-key
2. Put it into .env as `SERPAPI_KEY=xxx` (.env is git-ignored)
3. After searching price, result will be stored in ./results
4. Use view.py to view result
5. The free plan allows 250 searches per month, and one combination costs one
   search, so the cache below matters. Failed searches are not cached.
"""

folder = "./results"
Path(folder).mkdir(parents=True, exist_ok=True)


def load_api_key():
    """Read SERPAPI_KEY from the environment, falling back to ./.env"""
    key = os.environ.get("SERPAPI_KEY", "").strip()
    if not key and Path(".env").exists():
        for line in Path(".env").read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "SERPAPI_KEY":
                key = value.strip()
                break
    if not key:
        raise SystemExit("SERPAPI_KEY is not set. Add `SERPAPI_KEY=<key>` to ./.env")
    return key


# Get the API key from https://serpapi.com/manage-api-key
# The key is read from .env so it never ends up in version control.
token = load_api_key()

endpoint = "https://serpapi.com/search.json"

# SGN: 胡志明市國際機場
# TPE: 台北桃園國際機場
# YVR: 溫哥華國際機場
# HAN: 河內國際機場
# NRT: 東京成田機場
# KIX: 大阪關西機場
# AKL: 奧克蘭機場
# SYD: 雪梨機場
# MEL: 墨爾本機場
# BNE: 布里斯本機場

# Flight configurations: [origins, destinations, dates]
# Two limits the multi-city search enforces, worth knowing before editing this:
# - the dates must be ascending across the segments, otherwise the API answers 400
# - a date more than roughly 330 days out is not on sale yet and returns nothing
FLIGHT_CONFIGS = [
    {
        "origins": ["KIX"],
        "destinations": ["TPE"], 
        "dates": ["2026-09-10"],
    },
    {
        "origins": ["TPE"], 
        "destinations": ["AKL"],
        "dates": ["2026-09-24"],
    },
    {
        "origins": ["AKL"], 
        "destinations": ["TPE"],
        "dates": ["2026-10-08"],
    },
    {
        "origins": ["TPE"],
        "destinations": ["NRT"],
        "dates": ["2026-10-22"],
    },
]

def search(flights):
    """
    flights: list of dicts with keys: origin, destination, date
    """
    params = {
        "engine": "google_flights",
        "api_key": token,
        "type": "3",  # multi-city
        "multi_city_json": json.dumps(
            [
                {
                    "departure_id": flight["origin"],
                    "arrival_id": flight["destination"],
                    "date": flight["date"],
                }
                for flight in flights
            ]
        ),
        "adults": "2",
        "travel_class": "1",  # ECONOMY
        "currency": "TWD",
        "gl": "tw",
        "stops": "1",  # nonstop only, was maxNumberOfConnections: 0
        # CI: 中華航空
        # BR: 長榮航空
        # JX: 星宇航空
        # uncomment this line to limit airlines
        # "include_airlines": "BR,CI,JX",
    }

    res = urllib.request.urlopen(
        f"{endpoint}?{urllib.parse.urlencode(params)}", timeout=120
    )
    data = json.load(res)
    # The API answers 200 with an error field when a query returns nothing
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data


def generate_combinations(flight_configs, current_flights=None, flight_index=0):
    """
    Recursively generate all combinations of flights and search for each.

    Args:
        flight_configs: List of flight configuration dictionaries
        current_flights: Current combination being built
        flight_index: Index of current flight being processed
    """
    if current_flights is None:
        current_flights = []

    # Base case: all flights configured, perform search
    if flight_index >= len(flight_configs):
        # Create file prefix from flight details
        flight_details = []
        for flight in current_flights:
            flight_details.extend(
                [flight["origin"], flight["destination"], flight["date"]]
            )
        file_prefix = f"{folder}/{'_'.join(flight_details)}"

        # Check if already cached
        if Path(f"{file_prefix}_raw.json").exists():
            print(f"Skip {file_prefix} because cached")
            return

        # Perform search
        try:
            data = search(current_flights)
            print(f"Search {file_prefix}")
            with open(f"{file_prefix}_raw.json", "w") as f:
                f.write(json.dumps(data, indent=4, ensure_ascii=False))
        except Exception as e:
            print(f"Error searching {file_prefix}: {e}")
        return

    # Recursive case: try all combinations for current flight
    config = flight_configs[flight_index]

    for origin in config["origins"]:
        for destination in config["destinations"]:
            for date in config["dates"]:
                flight = {"origin": origin, "destination": destination, "date": date}
                generate_combinations(
                    flight_configs, current_flights + [flight], flight_index + 1
                )


# Start the recursive search
generate_combinations(FLIGHT_CONFIGS)
