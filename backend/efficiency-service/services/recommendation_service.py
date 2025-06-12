import logging
import logging_setup
import joblib
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from utils.terrain import group_highway_for_analysis, group_surface_for_analysis
from utils.models import get_model_paths 
from db.recommendation import (
    fetch_user_zone_segments, 
    fetch_activity_status, 
    update_prediction_and_activity_info,
    fetch_planned_segments_for_prediction,
    fetch_candidate_planned_activities
    )
from db.activities import fetch_all_user_ids

logger = logging.getLogger("app")

def train_model_for_user(user_id, engine):
    df = fetch_user_zone_segments(user_id, engine)
    # Keep only segments with efficiency medium, high or very high
    df = df[df["zone_among_similars"].isin(["medium", "high", "very_high"])]
    
    # Remove missing targets
    df = df.dropna(subset=["avg_speed", "avg_cadence"])
    
    if len(df) < 50:
        logger.warning(f"Unable to train model for user {user_id}: {len(df)} segments are not enough.")
        return
    
    logger.info(f"Training model for user {user_id} with {len(df)} segments")

    # Preprocessing
    df["grouped_highway"] = df["road_type"].apply(group_highway_for_analysis)
    df["grouped_surface"] = df.apply(lambda row: group_surface_for_analysis(row["surface_type"], row["road_type"]), axis=1)
    
    numeric_features = ['segment_length', 'avg_gradient', 'start_distance', 'start_altitude',
                    'temperature', 'humidity', 'wind', 'cumulative_ascent', 'cumulative_descent']
    categorical_features = ['grouped_highway', 'grouped_surface'] 
    
    X = df[numeric_features + categorical_features]
    y_cad = df["avg_cadence"]
    y_spd = df["avg_speed"]

    # Preprocessing pipeline
    def make_preprocessor():
        return ColumnTransformer([
            ("num", Pipeline([
                ("imputer", SimpleImputer(strategy="mean")),
                ("scaler", StandardScaler())
            ]), numeric_features),
            ("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore"))
            ]), categorical_features)
        ])

    pipeline_cad = Pipeline([
        ("preprocessor", make_preprocessor()),
        ("model",RandomForestRegressor(
            n_estimators=200,
            min_samples_split=10,
            min_samples_leaf=2,
            max_features='sqrt',
            max_depth=30,
            random_state=42
        ))
    ])

    pipeline_spd = Pipeline([
        ("preprocessor", make_preprocessor()),
        ("model", RandomForestRegressor(
            n_estimators=300,
            min_samples_split=5,
            min_samples_leaf=1,
            max_features='log2',
            max_depth=None,
            random_state=42
        ))
    ])

    pipeline_cad.fit(X, y_cad)
    pipeline_spd.fit(X, y_spd)

    model_cad_path, model_spd_path = get_model_paths(user_id)
    joblib.dump(pipeline_cad, model_cad_path)
    joblib.dump(pipeline_spd, model_spd_path)
    logger.info(f"Saved models for user {user_id} in {model_spd_path.parent}")

def should_run_regression_for_planned_activity(user_id, activity_id, engine):
    """
    Checks if a planned activity is ready and runs prediction if applicable.
    """
    if activity_id >= 0:
        return  # Not a planned activity

    status = fetch_activity_status(activity_id, engine)
    if not status:
        return

    if all(status[k] for k in ["segment_status", "terrain_status", "weather_status"]) and not status.get("not_processable"):
        logger.info(f"Running prediction for planned activity {activity_id}")
        predict_for_planned_activity(user_id, activity_id, engine)
    else:
        logger.info(f"Planned activity {activity_id} is not ready or marked as not_processable — skipping prediction")

def predict_for_planned_activity(user_id, activity_id, engine):
    """
    Applies saved recommendation models to segments of a planned activity.
    """
    logger.info(f"Starting prediction for planned activity {activity_id}")
    df = fetch_planned_segments_for_prediction(activity_id, engine)
    
    if df.empty:
        logger.warning(f"No segments found for activity {activity_id}")
        return

    models = load_saved_models(user_id, engine)
    if not models:
        logger.info(f"No saved models for user {user_id}")
        return
    
    df = df.sort_values("start_distance").reset_index(drop=True)
    df_features = df.copy()
    X = preprocess_segments_for_prediction(df_features)

    df["avg_speed"] = models.get("speed_model").predict(X) if "speed_model" in models else np.nan
    df["avg_cadence"] = models.get("cadence_model").predict(X) if "cadence_model" in models else np.nan

    # Compute duration, start_time and end_time
    df["estimated_time"] = df["segment_length"] / df["avg_speed"].replace(0, np.nan)
    df["start_time"] = np.cumsum([0] + df["estimated_time"].iloc[:-1].tolist())
    df["end_time"] = df["start_time"] + df["estimated_time"]

    # Clean invalid values
    invalid = df["estimated_time"].isna() | ~np.isfinite(df["estimated_time"])
    if invalid.any():
        logger.warning("Invalid or zero speeds found — nullifying time fields for affected segments.")
        df.loc[invalid, ["estimated_time", "start_time", "end_time"]] = None

    # Convert values for db insert
    for col in ["avg_speed", "avg_cadence", "start_time", "end_time"]:
        df[col] = df[col].apply(lambda x: None if pd.isna(x) or not np.isfinite(x) else x)

    # Prepare data
    update_cols = ["segment_id", "avg_speed", "avg_cadence", "start_time", "end_time", "segment_length", "end_distance", "cumulative_ascent"]
    segments_data = df[update_cols].to_dict("records")
    
    
    
    # Execute update
    update_prediction_and_activity_info(engine, activity_id, segments_data)

    logger.info(f"Completed prediction for activity {activity_id}")


def load_saved_models(user_id, engine=None):
    """
    Loads saved speed and cadence models for the given user_id from disk.
    Returns a dictionary with available models and required feature names.
    """
    models = {}
    # Get model paths
    model_cad_path, model_spd_path = get_model_paths(user_id)

    if os.path.exists(model_spd_path):
        speed_model = joblib.load(model_spd_path)
        models["speed_model"] = speed_model
        models["features"] = speed_model.feature_names_in_.tolist()
        logger.info(f"Loaded speed model for user {user_id}")
    else:
        logger.warning(f"No speed model found for user {user_id}")

    if os.path.exists(model_cad_path):
        cadence_model = joblib.load(model_cad_path)
        models["cadence_model"] = cadence_model
        if "features" not in models:  # reuse features only if not already set
            models["features"] = cadence_model.feature_names_in_.tolist()
        logger.info(f"Loaded cadence model for user {user_id}")
    else:
        logger.warning(f"No cadence model found for user {user_id}")

    return models if "features" in models else None

def preprocess_segments_for_prediction(df):
    """
    Prepares planned segments for prediction by adding engineered features
    and ensuring column consistency.
    """
    # Categorical grouping
    df["grouped_highway"] = df["road_type"].apply(group_highway_for_analysis)
    df["grouped_surface"] = df.apply(
        lambda row: group_surface_for_analysis(row["surface_type"], row["road_type"]),
        axis=1
    )

    # Returns only necessary columns
    feature_columns = [
        "segment_length", "avg_gradient", "start_distance", "start_altitude",
        "temperature", "humidity", "wind", "cumulative_ascent", "cumulative_descent",
        "grouped_highway", "grouped_surface"
    ]
    return df[feature_columns]

def run_batch_prediction_for_user(user_id, engine):
    """
    Fetches planned activities ready for recommendation and not predicted
    for a given user and triggers prediction.
    """
    activity_ids = fetch_candidate_planned_activities(user_id, engine)
    if not activity_ids:
        logger.info(f"No planned activities to predict for user {user_id}")
        return
    
    model_cad_path, model_spd_path = get_model_paths(user_id)

    if not model_spd_path.exists() or not model_cad_path.exists():
        logger.warning(f"No saved models for user {user_id} — checking if training is possible")
        train_model_for_user(user_id, engine)

        # Recheck
        if not model_spd_path.exists() or not model_cad_path.exists():
            logger.error(f"Training failed — models still not found for user {user_id}")
            return
        
    predicted = 0
    for activity_id in activity_ids:
        try:
            should_run_regression_for_planned_activity(user_id, activity_id, engine)
            predicted += 1
        except Exception as e:
            logger.error(f"Prediction failed for activity {activity_id}: {e}")

    logger.info(f"Predicted {predicted}/{len(activity_ids)} planned activities for user {user_id}")

def run_batch_prediction_all_users(engine):
    """
    Fetches all users from database and launches the batch prediction.
    """
    logger.info("Running batch prediction for planned activities...")
    user_ids = fetch_all_user_ids(engine)
    for user_id in user_ids:
        run_batch_prediction_for_user(user_id, engine)