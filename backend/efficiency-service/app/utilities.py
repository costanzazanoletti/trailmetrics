import pandas as pd
import gzip
import json


def parse_compressed_data(compressed_data):
    """Decompresses Gzip-encoded data and parses JSON into DataFrame."""
    try:
        decompressed = gzip.decompress(compressed_data)
        json_data = json.loads(decompressed.decode("utf-8"))
        
        if not json_data:
            raise Exception("No JSON data found in Kafka message")
        
        return pd.DataFrame(json_data)
        
    except (OSError, json.JSONDecodeError) as e:
        raise Exception(f"Error decompressing segments: {e}")
