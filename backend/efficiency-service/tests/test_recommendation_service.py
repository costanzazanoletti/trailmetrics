import pandas as pd
import pytest
from unittest.mock import patch
from services.recommendation_service import train_model_for_user

@pytest.fixture
def mock_df_from_csv():
    return pd.read_csv("tests/mock_segments_with_zones.csv")

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
    saved_paths = [call.args[1] for call in mock_dump.call_args_list]
    assert any(f"model_spd_user_{user_id}.pkl" in path for path in saved_paths)
    assert any(f"model_cad_user_{user_id}.pkl" in path for path in saved_paths)
