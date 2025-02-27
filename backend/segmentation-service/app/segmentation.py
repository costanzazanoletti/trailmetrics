import os
from dotenv import load_dotenv
from app.services.activity_service import get_activity_streams, preprocess_streams, create_segments
from app.database import store_segments

# Load environment variables from .env
load_dotenv()

def segment_activity(activity_id):
    """
    Retrieves and processes activity data, then segments it using predefined parameters.
    """
    df = get_activity_streams(activity_id)
    df = preprocess_streams(df)

    gradient_tolerance = float(os.getenv("GRADIENT_TOLERANCE", 0.5))
    min_segment_length = float(os.getenv("MIN_SEGMENT_LENGTH", 50.0))
    max_segment_length = float(os.getenv("MAX_SEGMENT_LENGTH", 200.0))
    classification_tolerance = float(os.getenv("CLASSIFICATION_TOLERANCE", 2.5))
    cadence_threshold = int(os.getenv("CADENCE_THRESHOLD", 60))
    cadence_tolerance = int(os.getenv("CADENCE_TOLERANCE", 5))
    rolling_window_size = int(os.getenv("ROLLING_WINDOW_SIZE", 0))

    segments_df= create_segments(df, activity_id, gradient_tolerance, min_segment_length, max_segment_length,
                                   classification_tolerance, cadence_threshold, cadence_tolerance, rolling_window_size)

    store_segments(segments_df)

    return segments_df