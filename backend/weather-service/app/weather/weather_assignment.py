import pandas as pd

def assign_weather_to_segments(segment_ids, weather_response_df):
    """
    Assigns weather data to segments
    """
    weather_data_repeated = pd.DataFrame([weather_response_df.iloc[0]] * len(segment_ids), columns=weather_response_df.columns)
    df_segments_ids = pd.DataFrame({"segment_id": segment_ids})
    return pd.concat([df_segments_ids.reset_index(drop=True), weather_data_repeated.reset_index(drop=True)], axis=1)