import pandas as pd
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
