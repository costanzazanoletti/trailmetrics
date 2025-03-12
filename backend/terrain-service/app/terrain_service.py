import pandas as pd
import json
import gzip
import logging
import logging_setup

# Setup logging
logger = logging.getLogger("app")

def get_terrain_info(activity_id, compressed_segments):
    """Main function to process the segments and collect terrain info."""
    logger.info(f"Processing Activity {activity_id}")
    try:
        df = parse_kafka_segments(compressed_segments)

        if df.empty:
            logger.warning(f"Empty segments for activity {activity_id}")
            return df
        return df
    except Exception as e:
        logger.error(f"Error in get_terrain_info: {e}")
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
