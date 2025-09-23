import requests
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

def geocode_address(address):
    """
    Geocodes an address to latitude and longitude.
    """
    try:
        geolocator = Nominatim(user_agent="poi_tool", timeout=10)
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        print(f"Error geocoding address: {e}")
        return None, None

def get_pois(latitude, longitude, distance_km=0.5):
    """
    Fetch POIs using the Overpass API within a square bounding box
    centered at (latitude, longitude) and extending distance_km in each
    cardinal direction.

    Returns a pandas DataFrame with columns: name, category, latitude,
    longitude, distance_from_center_km.
    """
    # Compute bounding box (south, west, north, east)
    north = geodesic(kilometers=distance_km).destination((latitude, longitude), 0).latitude
    south = geodesic(kilometers=distance_km).destination((latitude, longitude), 180).latitude
    east = geodesic(kilometers=distance_km).destination((latitude, longitude), 90).longitude
    west = geodesic(kilometers=distance_km).destination((latitude, longitude), 270).longitude

    south_west_north_east = (south, west, north, east)

    # Define categories of interest
    categories = ["amenity", "shop", "leisure", "tourism", "historic"]

    # Build Overpass QL query. Use out center to get centroids for ways/relations
    bbox_str = f"{south_west_north_east[0]},{south_west_north_east[1]},{south_west_north_east[2]},{south_west_north_east[3]}"
    selectors = []
    for key in categories:
        selectors.append(f"node[\"{key}\"]({bbox_str});")
        selectors.append(f"way[\"{key}\"]({bbox_str});")
        selectors.append(f"relation[\"{key}\"]({bbox_str});")
    union = "\n  ".join(selectors)

    overpass_query = f"""
    [out:json][timeout:30];
    (
      {union}
    );
    out center tags;
    """.strip()

    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": overpass_query},
            headers={"User-Agent": "poi_tool/1.0 (contact: example@example.com)"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        elements = data.get("elements", [])
        if not elements:
            return pd.DataFrame()

        results = []
        for el in elements:
            tags = el.get("tags", {})

            # Determine coordinates for node vs way/relation
            if el.get("type") == "node":
                poi_lat = el.get("lat")
                poi_lon = el.get("lon")
            else:
                center = el.get("center") or {}
                poi_lat = center.get("lat")
                poi_lon = center.get("lon")

            if poi_lat is None or poi_lon is None:
                continue

            # Determine best category present in tags
            category = "N/A"
            for cat in categories:
                if cat in tags:
                    category = cat
                    break

            name = tags.get("name", "N/A")
            dist_km = geodesic((latitude, longitude), (poi_lat, poi_lon)).km

            results.append({
                "name": name,
                "category": category,
                "latitude": poi_lat,
                "longitude": poi_lon,
                "distance_from_center_km": dist_km,
            })

        return pd.DataFrame(results)
    except Exception as e:
        print(f"An error occurred while fetching POIs: {e}")
        return pd.DataFrame()


def get_pois_with_detailed_categories(latitude, longitude, distance_km=0.5):
    """
    Fetch POIs using the Overpass API with detailed category mapping.
    Returns a pandas DataFrame with specific category assignments.
    """
    # Compute bounding box (south, west, north, east)
    north = geodesic(kilometers=distance_km).destination((latitude, longitude), 0).latitude
    south = geodesic(kilometers=distance_km).destination((latitude, longitude), 180).latitude
    east = geodesic(kilometers=distance_km).destination((latitude, longitude), 90).longitude
    west = geodesic(kilometers=distance_km).destination((latitude, longitude), 270).longitude

    south_west_north_east = (south, west, north, east)

    # Define comprehensive categories and their OSM mappings
    category_mappings = {
        "amenity": ["amenity"],
        "historic": ["historic"],
        "leisure": ["leisure"],
        "shop": ["shop"],
        "tourism": ["tourism"],
        "public_transport": ["public_transport", "route"],
        "highway": ["highway"],  # For bus stops, etc.
        "building": ["building"],  # For housing data
        "landuse": ["landuse"]  # For residential areas
    }

    # Build Overpass QL query
    bbox_str = f"{south_west_north_east[0]},{south_west_north_east[1]},{south_west_north_east[2]},{south_west_north_east[3]}"
    selectors = []
    for key_list in category_mappings.values():
        for key in key_list:
            selectors.append(f"node[\"{key}\"]({bbox_str});")
            selectors.append(f"way[\"{key}\"]({bbox_str});")
            selectors.append(f"relation[\"{key}\"]({bbox_str});")
    union = "\n  ".join(selectors)

    overpass_query = f"""
    [out:json][timeout:30];
    (
      {union}
    );
    out center tags;
    """.strip()

    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": overpass_query},
            headers={"User-Agent": "poi_tool/1.0 (contact: example@example.com)"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        elements = data.get("elements", [])
        if not elements:
            return pd.DataFrame()

        results = []
        for el in elements:
            tags = el.get("tags", {})

            # Determine coordinates for node vs way/relation
            if el.get("type") == "node":
                poi_lat = el.get("lat")
                poi_lon = el.get("lon")
            else:
                center = el.get("center") or {}
                poi_lat = center.get("lat")
                poi_lon = center.get("lon")

            if poi_lat is None or poi_lon is None:
                continue

            # Map to detailed categories
            detailed_category = map_to_detailed_category(tags)
            if detailed_category == "other":
                continue  # Skip items that don't fit our categories

            name = tags.get("name", "N/A")
            dist_km = geodesic((latitude, longitude), (poi_lat, poi_lon)).km

            results.append({
                "name": name,
                "category": detailed_category,
                "latitude": poi_lat,
                "longitude": poi_lon,
                "distance_from_center_km": dist_km,
            })

        return pd.DataFrame(results)
    except Exception as e:
        print(f"An error occurred while fetching POIs: {e}")
        return pd.DataFrame()


def map_to_detailed_category(tags):
    """
    Map OSM tags to detailed categories based on the requirements.
    """
    # Public Schools
    if tags.get("amenity") == "school" and tags.get("school:type") in ["public", "state"]:
        return "Public Schools"
    if tags.get("amenity") == "school" and not tags.get("school:type") in ["private", "religious"]:
        return "Public Schools"
    
    # Public Transit Lines
    if tags.get("public_transport") in ["station", "stop_position", "platform"]:
        return "Public Transit Lines"
    if tags.get("route") in ["subway", "bus", "tram", "light_rail"]:
        return "Public Transit Lines"
    if tags.get("highway") == "bus_stop":
        return "Public Transit Lines"
    
    # Parks and Recreational Areas
    if tags.get("leisure") in ["park", "recreation_ground", "playground", "garden"]:
        return "Parks and Recreational Areas"
    if tags.get("landuse") == "recreation_ground":
        return "Parks and Recreational Areas"
    
    # Community Services (Centers)
    if tags.get("amenity") in ["community_centre", "social_facility", "civic"]:
        return "Community Services"
    if tags.get("office") == "ngo":
        return "Community Services"
    
    # Cafés
    if tags.get("amenity") in ["cafe", "coffee_shop"]:
        return "Cafés"
    if tags.get("shop") == "coffee":
        return "Cafés"
    
    # Bars
    if tags.get("amenity") in ["bar", "pub", "nightclub"]:
        return "Bars"
    if tags.get("shop") == "alcohol":
        return "Bars"
    
    # Libraries
    if tags.get("amenity") == "library":
        return "Libraries"
    
    # Housing Categories
    if tags.get("building") == "house":
        return "Single-Family Houses"
    if tags.get("building") in ["apartments", "residential"]:
        return "Residential Buildings"
    if tags.get("building") == "detached":
        return "Detached Houses"
    if tags.get("building") == "semi_detached":
        return "Semi-Detached Houses"
    if tags.get("building") == "terrace":
        return "Terraced Houses"
    if tags.get("landuse") == "residential":
        return "Residential Areas"
    if tags.get("amenity") == "housing":
        return "Housing Facilities"
    
    # Original categories (keep for backward compatibility)
    if tags.get("amenity"):
        return "amenity"
    if tags.get("historic"):
        return "historic"
    if tags.get("leisure"):
        return "leisure"
    if tags.get("shop"):
        return "shop"
    if tags.get("tourism"):
        return "tourism"
    if tags.get("landuse"):
        return "landuse"
    
    return "other"


def create_grid_analysis(latitude, longitude, grid_size_km=0.5, search_radius_km=5.0):
    """
    Create a grid-based analysis of POIs around a center point.
    Returns a DataFrame with counts for each category in each grid cell.
    """
    # Calculate the number of grid cells in each direction
    half_grids = int(np.ceil(search_radius_km / grid_size_km))
    
    # Calculate grid boundaries
    north_bound = geodesic(kilometers=search_radius_km).destination((latitude, longitude), 0).latitude
    south_bound = geodesic(kilometers=search_radius_km).destination((latitude, longitude), 180).latitude
    east_bound = geodesic(kilometers=search_radius_km).destination((latitude, longitude), 90).longitude
    west_bound = geodesic(kilometers=search_radius_km).destination((latitude, longitude), 270).longitude
    
    # Create grid cells
    grid_results = []
    
    for i in range(-half_grids, half_grids + 1):
        for j in range(-half_grids, half_grids + 1):
            # Calculate grid cell center
            grid_center_lat = latitude + (i * grid_size_km / 111.0)  # Approximate km per degree
            grid_center_lon = longitude + (j * grid_size_km / (111.0 * np.cos(np.radians(latitude))))
            
            # Skip if outside search radius
            dist_from_center = geodesic((latitude, longitude), (grid_center_lat, grid_center_lon)).km
            if dist_from_center > search_radius_km:
                continue
            
            # Get POIs for this grid cell
            pois_df = get_pois_with_detailed_categories(grid_center_lat, grid_center_lon, grid_size_km/2)
            
            if not pois_df.empty:
                # Count POIs by category
                category_counts = pois_df['category'].value_counts()
                
                # Create row for this grid cell
                grid_row = {
                    'grid_center_lat': grid_center_lat,
                    'grid_center_lon': grid_center_lon,
                    'grid_id': f"grid_{i}_{j}",
                    'distance_from_center_km': dist_from_center
                }
                
                # Add counts for each category
                all_categories = [
                    "Public Schools", "Public Transit Lines", "Parks and Recreational Areas",
                    "Community Services", "Cafés", "Bars", "Libraries",
                    "Single-Family Houses", "Residential Buildings", "Detached Houses",
                    "Semi-Detached Houses", "Terraced Houses", "Residential Areas", "Housing Facilities",
                    "amenity", "historic", "leisure", "shop", "tourism", "landuse"
                ]
                
                for category in all_categories:
                    grid_row[f"{category}_count"] = category_counts.get(category, 0)
                
                grid_results.append(grid_row)
    
    return pd.DataFrame(grid_results)


def create_grid_analysis_vertical(latitude, longitude, grid_size_km=0.5, search_radius_km=5.0):
    """
    Create a grid-based analysis of POIs around a center point with vertical CSV format.
    Returns a DataFrame in long format with one row per POI per category.
    """
    # Calculate the number of grid cells in each direction
    half_grids = int(np.ceil(search_radius_km / grid_size_km))
    
    # Create grid cells
    grid_results = []
    
    for i in range(-half_grids, half_grids + 1):
        for j in range(-half_grids, half_grids + 1):
            # Calculate grid cell center
            grid_center_lat = latitude + (i * grid_size_km / 111.0)  # Approximate km per degree
            grid_center_lon = longitude + (j * grid_size_km / (111.0 * np.cos(np.radians(latitude))))
            
            # Skip if outside search radius
            dist_from_center = geodesic((latitude, longitude), (grid_center_lat, grid_center_lon)).km
            if dist_from_center > search_radius_km:
                continue
            
            # Get POIs for this grid cell
            pois_df = get_pois_with_detailed_categories(grid_center_lat, grid_center_lon, grid_size_km/2)
            
            if not pois_df.empty:
                # Group POIs by category and create one row per POI
                for _, poi in pois_df.iterrows():
                    grid_results.append({
                        'poi_lat': poi['latitude'],
                        'poi_lon': poi['longitude'],
                        'poi_name': poi['name'],
                        'grid_center_lat': grid_center_lat,
                        'grid_center_lon': grid_center_lon,
                        'grid_id': f"grid_{i}_{j}",
                        'distance_from_center_km': dist_from_center,
                        'category': poi['category'],
                        'count': 1  # Each POI counts as 1
                    })
    
    return pd.DataFrame(grid_results)
