import argparse
import glob
import json
from .geocode import cached_geocode
from .geometry import bbox_wgs84_for_square_m
from .tags import load_tag_filters, tagset_hash
from .overpass_client import OverpassClient
from .normalize import normalize_elements
from .io_utils import write_outputs
from .debug_repro import run_repro, compare_runs


def poiextract_cmd(argv=None):
    p = argparse.ArgumentParser(description='Deterministic 1x1 km OSM extractor')
    p.add_argument('--address', type=str)
    p.add_argument('--lat', type=float)
    p.add_argument('--lon', type=float)
    p.add_argument('--tags', type=str, default='config/tags.yml')
    p.add_argument('--overpass-url', type=str, default='https://overpass-api.de/api/interpreter')
    p.add_argument('--snapshot', type=str)
    p.add_argument('--outdir', type=str, default='out')
    args = p.parse_args(argv)

    if args.address and (args.lat is None or args.lon is None):
        lat, lon = cached_geocode(args.address)
    else:
        lat, lon = args.lat, args.lon

    south, west, north, east, utm_zone = bbox_wgs84_for_square_m(lat, lon, side_m=1000)
    filters = load_tag_filters(args.tags)
    tag_hash = tagset_hash(filters)
    client = OverpassClient(base_url=args.overpass_url)
    query = client.build_query((south, west, north, east), filters, snapshot_iso=(args.snapshot + 'T00:00:00Z') if args.snapshot else None)
    # Use chunked fetch to avoid Overpass OOM
    south, west, north, east, _ = (south, west, north, east, utm_zone)
    data = client.fetch_all_chunked((south, west, north, east), filters, snapshot_iso=(args.snapshot + 'T00:00:00Z') if args.snapshot else None, chunk_size=1)
    elements = data.get('elements', [])
    rows = normalize_elements(elements)
    meta = {
        'input_address': args.address or '',
        'center_lat': lat,
        'center_lon': lon,
        'utm_zone': utm_zone,
        'bbox_wgs84': [south, west, north, east],
        'tagset_hash': tag_hash,
        'overpass_url': args.overpass_url,
        'osm_base_ts': data.get('osm3s', {}).get('timestamp_osm_base'),
    }
    write_outputs(rows, args.outdir, meta)


def poiextract_repro_cmd(argv=None):
    p = argparse.ArgumentParser(description='Reproducibility harness')
    p.add_argument('--address', type=str)
    p.add_argument('--lat', type=float)
    p.add_argument('--lon', type=float)
    p.add_argument('--tags', type=str, default='config/tags.yml')
    p.add_argument('--runs', type=int, default=5)
    p.add_argument('--snapshot', type=str)
    p.add_argument('--outdir', type=str, default='logs/repro')
    args = p.parse_args(argv)
    if args.address and (args.lat is None or args.lon is None):
        lat, lon = cached_geocode(args.address)
    else:
        lat, lon = args.lat, args.lon
    run_repro(args.address, lat, lon, args.tags, runs=args.runs, snapshot_iso=(args.snapshot + 'T00:00:00Z') if args.snapshot else None, out_dir=args.outdir)
    d = sorted(glob.glob(args.outdir + '/*'))[-1]
    print(json.dumps(compare_runs(d), indent=2))


def poiextract_compare_cmd(argv=None):
    p = argparse.ArgumentParser(description='Compare repro runs')
    p.add_argument('--dir', type=str, required=True)
    args = p.parse_args(argv)
    print(json.dumps(compare_runs(args.dir), indent=2))


