import pandas as pd
import numpy as np
from app.database import get_raw_activity_streams

def get_activity_streams(activity_id):
    """
    Converts raw activity stream data into a structured format.
    """
    df_streams = get_raw_activity_streams(activity_id)

    activity_data = {}

    for _, row in df_streams.iterrows():
        stream_type = row["type"]
        values = row["data"]

        # Only parse if it's a string; otherwise, assume it's already a list
        if isinstance(values, str):
            import ast
            values = ast.literal_eval(values)

        activity_data[stream_type] = values

    max_length = max(len(v) for v in activity_data.values())

    structured_data = {
        key: (value if len(value) == max_length else [None] * max_length)
        for key, value in activity_data.items()
    }

    structured_data["activity_id"] = [activity_id] * max_length

    return pd.DataFrame(structured_data)

def preprocess_streams(df):
    """
    Preprocesses the dataframe before segmenting:
    - Renames columns: 'grade_smooth' -> 'grade', 'velocity_smooth' -> 'speed'.
    - Checks for missing values in essential columns.
    - Fills missing values to ensure lists are of the same length.
    """
    df = df.rename(columns={"grade_smooth": "grade", "velocity_smooth": "speed"})
    
    required_columns = ["distance", "altitude", "latlng", "cadence"]
    missing_columns = [col for col in required_columns if col in df.columns and df[col].isnull().all()]
    
    if missing_columns:
        raise ValueError(f"Cannot process activity: missing all values in {missing_columns}")
    
    numeric_cols = df.select_dtypes(include=["number"]).columns
    df[numeric_cols] = df[numeric_cols].infer_objects(copy=False)

    for col in required_columns:
        if col in df.columns and df[col].dtype != "O":  # Exclude object columns like "latlng"
            df[col] = df[col].interpolate().bfill().ffill()
            
    return df

def create_segments(df, activity_id, gradient_tolerance, min_segment_length, max_segment_length,
                            classification_tolerance, cadence_threshold, cadence_tolerance, rolling_window_size):
    """
    Segments a single activity based on gradient and cadence changes, with configurable parameters.
    """
    df = df.sort_values("distance").reset_index(drop=True)
    
    if rolling_window_size > 1:
        df["grade"] = df["grade"].rolling(window=rolling_window_size, center=True, min_periods=1).mean()
        df["cadence"] = df["cadence"].rolling(window=rolling_window_size, center=True, min_periods=1).mean()
    
    segments = []
    start_index = 0
    
    for i in range(1, len(df)):
        segment_length = df["distance"].iloc[i] - df["distance"].iloc[start_index]
        
        grade_change = abs(df["grade"].iloc[i] - df["grade"].iloc[i - 1])
        cadence_change = abs(df["cadence"].iloc[i] - df["cadence"].iloc[i - 1])
        
        if ((grade_change > gradient_tolerance or cadence_change > cadence_tolerance)
            and segment_length >= min_segment_length) or segment_length > max_segment_length:
            
            avg_gradient = np.mean(df["grade"].iloc[start_index:i])
            avg_cadence = np.mean(df["cadence"].iloc[start_index:i])
            
            movement_type = "running" if avg_cadence > cadence_threshold else "walking"
            segment_type = "uphill" if avg_gradient > 0 else "downhill" if avg_gradient < 0 else "flat"
            
            segment = {
                "activity_id": activity_id,
                "start_distance": df["distance"].iloc[start_index],
                "end_distance": df["distance"].iloc[i - 1],
                "segment_length": segment_length,
                "avg_gradient": avg_gradient,
                "avg_cadence": avg_cadence,
                "movement_type": movement_type,
                "type": segment_type,
                "grade_category": round(avg_gradient / classification_tolerance) * classification_tolerance
            }
            segments.append(segment)
            start_index = i
    
    segments_df = pd.DataFrame(segments)
    return segments_df[segments_df["segment_length"] >= min_segment_length].reset_index(drop=True) if not segments_df.empty else pd.DataFrame()
