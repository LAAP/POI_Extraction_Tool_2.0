import os
import json
from typing import Tuple
from geopy.geocoders import Nominatim


def _cache_path() -> str:
    base = os.path.join(os.path.dirname(__file__), '..', '.cache')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, 'geocode.json')


def cached_geocode(address: str) -> Tuple[float, float]:
    path = _cache_path()
    cache = {}
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                cache = json.load(f) or {}
        except Exception:
            cache = {}
    if address in cache:
        lat, lon = cache[address]
        return float(lat), float(lon)
    geolocator = Nominatim(user_agent="poi_tool_deterministic", timeout=15)
    loc = geolocator.geocode(address, exactly_one=True, addressdetails=False)
    if not loc:
        return None, None
    cache[address] = [loc.latitude, loc.longitude]
    try:
        with open(path, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass
    return float(loc.latitude), float(loc.longitude)


