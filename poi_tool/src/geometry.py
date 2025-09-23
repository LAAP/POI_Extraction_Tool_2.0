from typing import Tuple
from pyproj import CRS, Transformer


def latlon_to_utm_zone(lat: float, lon: float) -> CRS:
    """
    Return the UTM CRS for the given WGS84 lat/lon, northern/southern hemisphere aware.
    Deterministic: no randomness.
    """
    zone = int((lon + 180) // 6) + 1
    is_northern = lat >= 0
    return CRS.from_dict({
        "proj": "utm",
        "zone": zone,
        "datum": "WGS84",
        "units": "m",
        "north": is_northern
    })


def bbox_wgs84_for_square_m(center_lat: float, center_lon: float, side_m: int = 1000) -> Tuple[float, float, float, float, int]:
    """
    Compute a 1x1 km (or side_m) square bbox centered on WGS84 coord using UTM meters to avoid drift.
    Returns (south, west, north, east, utm_zone) with 8-decimal rounding applied to all bbox coords.
    """
    wgs84 = CRS.from_epsg(4326)
    utm = latlon_to_utm_zone(center_lat, center_lon)
    to_utm = Transformer.from_crs(wgs84, utm, always_xy=True)
    to_wgs = Transformer.from_crs(utm, wgs84, always_xy=True)

    cx, cy = to_utm.transform(center_lon, center_lat)
    half = side_m / 2.0
    minx, miny = cx - half, cy - half
    maxx, maxy = cx + half, cy + half

    west, south = to_wgs.transform(minx, miny)
    east, north = to_wgs.transform(maxx, maxy)

    def r8(v: float) -> float:
        return float(f"{v:.8f}")

    return r8(south), r8(west), r8(north), r8(east), int(utm.to_authority()[1])


