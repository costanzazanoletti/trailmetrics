import pytest
import pandas as pd
import numpy as np
from app.services.activity_service import preprocess_streams, create_segments

# Sample activity data based on the uploaded CSV
mock_data = {
    "latlng": [[46.142836, 8.469562], [46.142853, 8.469612], [46.142875, 8.469717], [46.142875, 8.469759], [46.142875, 8.469759]],
    "velocity_smooth": [0.0, 0.0, 2.3, 2.2, 2.5],
    "grade_smooth": [2.6, np.nan, 1.6, np.nan, 0.6],  # Introduce missing values
    "cadence": [55, np.nan, np.nan, 82, 82],  # Missing cadence values
    "heartrate": [80, 80, 84, 88, 91],
    "altitude": [904.6, 904.7, np.nan, 904.9, np.nan],  # Missing altitude values
    "distance": [1.0, 4.7, 12.6, 15.8, 19.5],
    "time": [0, 1, 5, 6, 7],
    "activity_id": [5727925996] * 5
}

# Convert to DataFrame
mock_df = pd.DataFrame(mock_data)

def test_preprocess_streams():
    df_processed = preprocess_streams(mock_df)

    required_columns = ["distance", "altitude", "latlng", "cadence"]
    
    for col in required_columns:
        assert col in df_processed.columns, f"Missing required column: {col}"
    
    assert not df_processed[required_columns].isnull().values.any(), "There are still missing values after preprocessing"

    print("Processed DataFrame:")
    print(df_processed.head())

def test_create_segments():
    # Define test parameters
    activity_id = 5727925996
    gradient_tolerance = 0.5
    min_segment_length = 10.0
    max_segment_length = 200.0
    classification_tolerance = 2.5
    cadence_threshold = 60
    cadence_tolerance = 5
    rolling_window_size = 1

    # Ensure data is preprocessed
    df_preprocessed = preprocess_streams(mock_df)

    # Call the segmentation function
    segments_df = create_segments(
        df_preprocessed, activity_id, gradient_tolerance, min_segment_length, max_segment_length,
        classification_tolerance, cadence_threshold, cadence_tolerance, rolling_window_size
    )

    assert not segments_df.empty, "Segmentation should return some segments"
    assert "segment_length" in segments_df.columns, "Missing 'segment_length' column"
    assert "avg_gradient" in segments_df.columns, "Missing 'avg_gradient' column"
    assert "movement_type" in segments_df.columns, "Missing 'movement_type' column"

    print("Segmented Activity Data:")
    print(segments_df.head())
