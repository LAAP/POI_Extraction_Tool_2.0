import os
import csv
import json
import hashlib
from typing import List, Dict, Tuple


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def write_outputs(rows: List[Dict], out_dir: str, meta: Dict) -> Tuple[str, str]:
    ensure_dir(out_dir)
    # Stable ID hash
    ids = [f"{r['type']}:{r['id']}" for r in rows]
    id_list_sha256 = hashlib.sha256("|".join(ids).encode('utf-8')).hexdigest()
    meta = dict(meta)
    meta['id_list_sha256'] = id_list_sha256

    csv_path = os.path.join(out_dir, 'pois.csv')
    json_path = os.path.join(out_dir, 'pois.json')

    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([
            '# input_address', meta.get('input_address', ''),
            'center_lat', meta.get('center_lat', ''),
            'center_lon', meta.get('center_lon', ''),
            'utm_zone', meta.get('utm_zone', ''),
            'bbox_wgs84', json.dumps(meta.get('bbox_wgs84', [])),
            'tagset_hash', meta.get('tagset_hash', ''),
            'overpass_url', meta.get('overpass_url', ''),
            'osm_base_ts', meta.get('osm_base_ts', ''),
            'id_list_sha256', id_list_sha256,
        ])
        w.writerow(['type', 'id', 'lat', 'lon', 'name'])
        for r in rows:
            w.writerow([r['type'], r['id'], f"{r['lat']:.8f}", f"{r['lon']:.8f}", r['name']])

    with open(json_path, 'w') as f:
        json.dump({'meta': meta, 'rows': rows}, f, indent=2)

    return csv_path, json_path


