from __future__ import annotations

import time
import hashlib
from typing import Dict, List, Tuple, Optional

import httpx


class OverpassClient:
    def __init__(self, base_url: str = "https://overpass-api.de/api/interpreter", timeout_s: int = 180):
        self.base_url = base_url
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "poi_tool/1.0 (deterministic-fetch)",
        }

    def build_query(self, bbox: Tuple[float, float, float, float], filters: List[str], snapshot_iso: Optional[str] = None) -> str:
        south, west, north, east = bbox
        date_clause = f'[date:"{snapshot_iso}"]' if snapshot_iso else ''
        union = "\n  ".join([f"node{flt}({south},{west},{north},{east});\n  way{flt}({south},{west},{north},{east});\n  relation{flt}({south},{west},{north},{east});" for flt in filters])
        q = f"""
        [out:json][timeout:{self.timeout_s}]{date_clause};
        (
          {union}
        );
        out center tags;
        """.strip()
        return q

    def fetch(self, query: str, max_retries: int = 5) -> Dict:
        backoff = 1.0
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=self.timeout_s) as client:
                    r = client.post(self.base_url, data={"data": query}, headers=self._headers())
                if r.status_code in (429, 504, 502, 503):
                    raise httpx.HTTPStatusError("Overpass busy", request=r.request, response=r)
                r.raise_for_status()
                data = r.json()
                # Completeness checks
                if 'remark' in data and any(k in str(data['remark']).lower() for k in ["too many", "timeout", "runtime error", "limited"]):
                    raise RuntimeError(f"Overpass remark indicates truncation: {data['remark']}")
                if 'elements' not in data:
                    raise RuntimeError("Overpass returned no elements")
                return data
            except Exception as e:
                last_exc = e
                time.sleep(backoff)
                backoff = min(backoff * 2.0, 30.0)
        assert last_exc is not None
        raise last_exc

    @staticmethod
    def elements_id_hash(elements: List[Dict]) -> str:
        type_order = {"node": "0", "way": "1", "relation": "2"}
        ids = [f"{type_order.get(el.get('type',''), '9')}:{el.get('id','')}" for el in elements]
        ids.sort()
        concat = "|".join(ids)
        return hashlib.sha256(concat.encode('utf-8')).hexdigest()

    def fetch_all_chunked(self, bbox: Tuple[float, float, float, float], filters: List[str], snapshot_iso: Optional[str] = None, chunk_size: int = 4) -> Dict:
        """
        Split the big union into multiple smaller queries to avoid OOM on Overpass.
        Aggregate elements and osm3s metadata; last osm3s wins.
        """
        all_elements: Dict[Tuple[str, int], Dict] = {}
        osm3s = {}
        for i in range(0, len(filters), chunk_size):
            chunk = filters[i:i+chunk_size]
            q = self.build_query(bbox, chunk, snapshot_iso=snapshot_iso)
            data = self.fetch(q)
            osm3s = data.get('osm3s', osm3s)
            for el in data.get('elements', []):
                key = (el.get('type'), el.get('id'))
                if key[0] is None or key[1] is None:
                    continue
                all_elements[key] = el
        return { 'osm3s': osm3s, 'elements': list(all_elements.values()) }


