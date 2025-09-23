import os
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict

from .geometry import bbox_wgs84_for_square_m
from .overpass_client import OverpassClient
from .tags import load_tag_filters, tagset_hash


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def run_repro(address: Optional[str], lat: Optional[float], lon: Optional[float], tags_path: str, runs: int = 5, snapshot_iso: Optional[str] = None, out_dir: str = "logs/repro"):
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    run_dir = os.path.join(out_dir, ts)
    ensure_dir(run_dir)

    # Resolve center
    center_lat = lat if lat is not None else 0.0
    center_lon = lon if lon is not None else 0.0

    bbox = bbox_wgs84_for_square_m(center_lat, center_lon, side_m=1000)
    south, west, north, east, utm_zone = bbox

    filters = load_tag_filters(tags_path)
    tag_hash = tagset_hash(filters)

    client = OverpassClient()
    query = client.build_query((south, west, north, east), filters, snapshot_iso=snapshot_iso)

    for i in range(runs):
        data = client.fetch(query)
        elements = data.get('elements', [])
        id_hash = client.elements_id_hash(elements)
        rec = {
            'run': i,
            'bbox': [south, west, north, east],
            'utm_zone': utm_zone,
            'overpass_url': client.base_url,
            'osm_base_ts': data.get('osm3s', {}).get('timestamp_osm_base'),
            'elements_count': len(elements),
            'id_hash': id_hash,
        }
        with open(os.path.join(run_dir, f'run_{i}.json'), 'w') as f:
            json.dump(rec, f, indent=2)


def compare_runs(run_dir: str) -> Dict:
    runs: List[Dict] = []
    for fn in sorted(os.listdir(run_dir)):
        if fn.endswith('.json'):
            with open(os.path.join(run_dir, fn), 'r') as f:
                runs.append(json.load(f))
    hashes = [r['id_hash'] for r in runs]
    stable = len(set(hashes)) == 1
    return { 'runs': len(runs), 'stable': stable, 'hashes': hashes }


