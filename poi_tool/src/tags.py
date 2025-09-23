from typing import List
import hashlib
import yaml


def load_tag_filters(path: str) -> List[str]:
    with open(path, 'r') as f:
        cfg = yaml.safe_load(f) or {}
    filters: List[str] = []
    for entry in cfg.get('tags', []):
        # entry like: { key: amenity, values: [cafe, bar] } OR { key: shop }
        key = entry.get('key')
        values = entry.get('values')
        if key and values:
            for v in values:
                filters.append(f'["{key}"="{v}"]')
        elif key:
            filters.append(f'["{key}"]')
    # dedupe deterministically
    filters = sorted(set(filters))
    return filters


def tagset_hash(filters: List[str]) -> str:
    s = "|".join(filters)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


