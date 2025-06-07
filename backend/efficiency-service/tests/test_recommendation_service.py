import pandas as pd
import pytest
from unittest.mock import patch
from db.setup import engine
from db.core import execute_sql, fetch_one_sql, fetch_all_sql_df
from services.segments_service import process_segments
from services.recommendation_service import (
    train_model_for_user,
    predict_for_planned_activity,
    should_run_regression_for_planned_activity
)

@patch("services.recommendation_service.fetch_user_zone_segments")
def test_train_model_for_user(mock_fetch, mock_df_from_csv, tmp_path):
    mock_fetch.return_value = mock_df_from_csv
    user_id = "999"

    # Change working dir temporarily to isolate the model files
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    
    with patch("os.makedirs") as mock_makedirs, \
         patch("joblib.dump") as mock_dump:
        # Execute training
        train_model_for_user(user_id, engine=None)
    
    # Assertions
    assert mock_dump.call_count == 2
    saved_paths = [str(call.args[1]) for call in mock_dump.call_args_list]
    assert any(f"model_spd_user_{user_id}.pkl" in path for path in saved_paths)
    assert any(f"model_cad_user_{user_id}.pkl" in path for path in saved_paths)

@pytest.mark.parametrize("load_sample_segments", ["mock_planned_message.json"], indirect=True)
def test_predict_for_planned_activity(load_sample_segments, dummy_model_files, set_up):
    # Setup
    activity_id, user_id, compressed_segments, is_planned = load_sample_segments
    user_id = dummy_model_files
    process_segments(activity_id, True, user_id, compressed_segments, engine)

    # Insert activity ready
    with engine.begin() as connection:
        query = """
            INSERT INTO activity_status_tracker(activity_id, segment_status, terrain_status, weather_status)
            VALUES (:activity_id, TRUE, TRUE, TRUE)
            ON CONFLICT (activity_id) DO UPDATE 
            SET segment_status = TRUE, terrain_status = TRUE, weather_status = TRUE
        """
        execute_sql(connection, query, {"activity_id": activity_id})

    # Execute
    predict_for_planned_activity(user_id, activity_id, engine)

    # Check
    with engine.begin() as connection:
        df = fetch_all_sql_df(connection, "SELECT * FROM segments WHERE activity_id = :id", {"id": activity_id})
        status = fetch_one_sql(connection, """
            SELECT prediction_executed_at FROM activity_status_tracker WHERE activity_id = :id
        """, {"id": activity_id})[0]

    assert not df["avg_speed"].isnull().all()
    assert not df["avg_cadence"].isnull().all()
    assert status is not None


@pytest.mark.parametrize("segment, terrain, weather, not_proc, expect_called", [
    (True, True, True, False, True),
    (True, False, True, False, False),
    (True, True, True, True, False),
])
def test_should_run_regression_for_planned_activity(segment, terrain, weather, not_proc, expect_called):
    activity_id = -999999  # planned
    user_id = 123

    # Insert a fake status
    with engine.begin() as connection:
        execute_sql(connection, """
            INSERT INTO activity_status_tracker(activity_id, segment_status, terrain_status, weather_status, not_processable)
            VALUES (:id, :s, :t, :w, :n)
            ON CONFLICT (activity_id) DO UPDATE 
            SET segment_status = :s, terrain_status = :t, weather_status = :w, not_processable = :n
        """, {"id": activity_id, "s": segment, "t": terrain, "w": weather, "n": not_proc})

    # Mock the function that needs to be called
    with patch("services.recommendation_service.predict_for_planned_activity") as mock_predict:
        should_run_regression_for_planned_activity(user_id, activity_id, engine)
        assert mock_predict.called == expect_called
