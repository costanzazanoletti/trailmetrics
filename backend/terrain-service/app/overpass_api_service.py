import requests
import time
import logging
import logging_setup
import os
import pandas as pd
from shapely.geometry import LineString
from dotenv import load_dotenv
from collections import defaultdict


# Setup logging
logger = logging.getLogger("app")
# Load environment variables
load_dotenv()

OVERPASS_URL = os.getenv("OVERPASS_API_URL")

# Initialize the cache for most frequent surface by highway
surface_cache = defaultdict(lambda: defaultdict(int))
most_frequent_surface = {}

def fetch_overpass_data(query, max_retries=3):
    """Sends a request to Overpass API and returns the response JSON."""
    for attempt in range(max_retries):
        try:
            response = requests.get(OVERPASS_URL, params={'data': query}, timeout=30)
            response.raise_for_status()  # Generates an error if the request fails
            
            data = response.json()
            if "elements" in data and data["elements"]:
                return data  # Returns data if valid
            
            logger.warning("Overpass API returned an empty response.")
            return None  # No data found

        except requests.exceptions.RequestException as e:
            logger.error(f"Overpass request failed (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(2 ** attempt)  # Retry with exponential backoff

    logger.error("Max retries reached. Overpass API request failed.")
    return None

def build_overpass_query(min_lat, min_lng, max_lat, max_lng):
    """Builds an Overpass API query to fetch highway and surface info in a bounding box."""
    query = f"""
    [out:json];
    (
      way["highway"]({min_lat},{min_lng},{max_lat},{max_lng});
    );
    out body;
    >;
    out skel qt;
    """
    return query

def update_surface_cache(highway, surface):
    if highway and surface:
        surface_cache[highway][surface] += 1

def get_most_frequent_surface(highway):
    if highway in surface_cache and surface_cache[highway]:
        return max(surface_cache[highway], key=surface_cache[highway].get)
    return None

def assign_terrain_info(df_segments, way_geometries):
    """Assigns Overpass terrain data (highway, surface) to segments in the DataFrame."""
    df = df_segments.copy()
    df["highway"] = None
    df["surface"] = None

    # Assign the terrain to the closest segments
    for index, row in df.iterrows():
        segment_line = LineString([(row["start_lng"], row["start_lat"]), (row["end_lng"], row["end_lat"])])
        
        closest_way = None
        min_distance = float("inf")

        for way in way_geometries:
            distance = segment_line.distance(way["geometry"])  # Distance between geometry and way
            if distance < min_distance:
                min_distance = distance
                closest_way = way

        if closest_way:
            df.at[index, "highway"] = closest_way["highway"]
            df.at[index, "surface"] = closest_way["surface"]
            if pd.isna(df.at[index, "surface"]) and closest_way["highway"]:
                inferred_surface = get_most_frequent_surface(closest_way["highway"])
                if inferred_surface:
                    logger.info(f"Infer surface from highway {closest_way["highway"]}: {inferred_surface}")
                    df.at[index, "surface"] = inferred_surface

    return df




def extract_way_geometries(terrain_data):
    """Extracts way geometries from Overpass data, associating nodes with their coordinates."""
    
    # Create a dictionary {node_id: (lat, lon)} for fast search
    node_coords = {
        node["id"]: (node["lon"], node["lat"])
        for node in terrain_data if node["type"] == "node"
    }

    way_geometries = []

    # Process each way
    for element in terrain_data:
        if element["type"] == "way" and "nodes" in element and "tags" in element:
            highway = element["tags"].get("highway")
            surface = element["tags"].get("surface")
            if highway and surface:
                update_surface_cache(highway, surface)

            coords = [node_coords[nid] for nid in element["nodes"] if nid in node_coords]

            if len(coords) >= 2:
                way_geometries.append({
                    "way_id": element["id"],
                    "geometry": LineString(coords),
                    "highway": highway,
                    "surface": surface
                })
    # After processing all ways, calculate the most frequent surface for each highway
    for highway, surface_counts in surface_cache.items():
        most_frequent_surface[highway] = max(surface_counts, key=surface_counts.get)

    return way_geometries
