from src.geometry import bbox_wgs84_for_square_m
from src.normalize import normalize_elements
from src.overpass_client import OverpassClient


def test_grid_construction_consistency():
    b1 = bbox_wgs84_for_square_m(40.0, -74.0, 1000)
    b2 = bbox_wgs84_for_square_m(40.0, -74.0, 1000)
    assert b1 == b2


def test_sorting_and_dedup():
    els = [
        {"type": "way", "id": 2, "center": {"lat": 1.0, "lon": 1.0}, "tags": {"name": "B"}},
        {"type": "node", "id": 1, "lat": 0.0, "lon": 0.0, "tags": {"name": "A"}},
        {"type": "relation", "id": 3, "center": {"lat": 2.0, "lon": 2.0}},
        {"type": "node", "id": 1, "lat": 0.0, "lon": 0.0},
    ]
    rows = normalize_elements(els)
    ids = [(r['type'], r['id']) for r in rows]
    assert ids == [("node", 1), ("way", 2), ("relation", 3)]


def test_snapshot_flag_builds_date_clause():
    c = OverpassClient()
    q = c.build_query((0,0,1,1), ['["amenity"]'], snapshot_iso='2025-09-01T00:00:00Z')
    assert '[date:"2025-09-01T00:00:00Z"]' in q


