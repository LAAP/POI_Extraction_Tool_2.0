from typing import Dict, List, Tuple


TYPE_ORDER = {"node": 0, "way": 1, "relation": 2}


def _extract_coords(el: Dict) -> Tuple[float, float]:
    if el.get('type') == 'node':
        return float(el.get('lon')), float(el.get('lat'))
    center = el.get('center') or {}
    return float(center.get('lon')), float(center.get('lat'))


def normalize_elements(elements: List[Dict]) -> List[Dict]:
    dedup: Dict[Tuple[str, int], Dict] = {}
    for el in elements:
        etype = el.get('type')
        eid = el.get('id')
        if etype not in TYPE_ORDER or eid is None:
            continue
        lon, lat = _extract_coords(el)
        tags = el.get('tags', {}) or {}
        name = tags.get('name', 'N/A')
        key = (etype, eid)
        dedup[key] = {
            'type': etype,
            'id': int(eid),
            'lat': lat,
            'lon': lon,
            'name': name,
            'tags': tags,
        }
    rows = list(dedup.values())
    rows.sort(key=lambda r: (TYPE_ORDER[r['type']], r['id']))
    return rows


