import pandas as pd
import numpy as np
import json
import gzip
import logging
import logging_setup
from app.overpass_api_service import build_overpass_query, fetch_overpass_data, assign_terrain_info, extract_way_geometries

# Setup logging
logger = logging.getLogger("app")

def get_terrain_info(activity_id, compressed_segments):
    """Main function to process the segments and collect terrain info."""
    logger.info(f"Processing Activity {activity_id}")
    
    try:
        df_segments = parse_kafka_segments(compressed_segments)
        if df_segments.empty:
            logger.warning(f"Empty segments for activity {activity_id}")
            return df_segments

        # Compute min/max latitudine and longitude for the activity
        min_lat, max_lat = df_segments["start_lat"].min(), df_segments["end_lat"].max()
        min_lng, max_lng = df_segments["start_lng"].min(), df_segments["end_lng"].max()

        # Generate bounding boxes to split the area (0.1 step is about 11 km but can change with the longitude)
        bounding_boxes = create_bounding_boxes(min_lat, max_lat, min_lng, max_lng, lat_step=0.1, lng_step=0.1)
        logger.info(f"Generated {len(bounding_boxes)} bounding boxes for Overpass queries.")

        # Call Overpass API for each bounding box
        terrain_data = []
        for bbox in bounding_boxes:
            query = build_overpass_query(*bbox)
            response = fetch_overpass_data(query)

            if response and "elements" in response:
                terrain_data.extend(response["elements"])

        if not terrain_data:
            logger.warning(f"No terrain data found for activity {activity_id}")
            return df_segments 

        # Extract geometries from Overpass wa
        way_geometries = extract_way_geometries(terrain_data)

        # Associate segments to closest ways
        df_final = assign_terrain_info(df_segments, way_geometries)
        return df_final

    except Exception as e:
        logger.error(f"Error in get_terrain_info: {e}", exc_info=True)
        return pd.DataFrame()


    
def parse_kafka_segments(compressed_segments):
    """Parses the decompressed JSON segments into a DataFrame."""
    segments_list = decompress_segments(compressed_segments) 

    if not segments_list:
        print("No segments found") 
        return pd.DataFrame()
    
    df = pd.DataFrame(segments_list)
    return df
    
def decompress_segments(compressed_segments):
    """Decompresses Gzip-encoded activity segments."""
    try:
        decompressed = gzip.decompress(compressed_segments)
        return json.loads(decompressed.decode("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error decompressing segments: {e}")
        return None


def create_bounding_boxes(min_lat, max_lat, min_lng, max_lng, lat_step=0.1, lng_step=0.1):
    """Divide the activity area into smaller bounding boxes."""
    bounding_boxes = []
    
    latitudes = np.arange(min_lat, max_lat, lat_step)
    longitudes = np.arange(min_lng, max_lng, lng_step)
    
    for lat in latitudes:
        for lng in longitudes:
            bounding_boxes.append((lat, lng, min(lat + lat_step, max_lat), min(lng + lng_step, max_lng)))

    return bounding_boxes
