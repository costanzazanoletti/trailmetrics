import logging
import logging_setup
import joblib
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from utils.terrain import group_highway_for_analysis, group_surface_for_analysis
from utils.models import get_model_paths 
from db.recommendation import (
    fetch_user_zone_segments, 
    fetch_activity_status, 
    update_segment_predictions,
    fetch_planned_segments_for_prediction,
    fetch_candidate_planned_activities
    )
from db.activities import fetch_all_user_ids

logger = logging.getLogger("app")

def train_model_for_user(user_id, engine):
    df = fetch_user_zone_segments(user_id, engine)
    
    if len(df) < 50:
        logger.warning(f"Unable to train model for user {user_id}: {len(df)} segments are not enough.")
        return
    
    logger.info(f"Training model for user {user_id}")


    # Preprocessing
    df['grouped_highway'] = df['road_type'].apply(group_highway_for_analysis)
    df['grouped_surface'] = df.apply(lambda row: group_surface_for_analysis(row['surface_type'], row['road_type']), axis=1)
    
    numeric_features = ['segment_length', 'avg_gradient', 'start_distance', 'start_altitude',
                    'temperature', 'humidity', 'wind', 'cumulative_ascent', 'cumulative_descent']
    categorical_features = ['grouped_highway', 'grouped_surface'] 
    
    X = df[numeric_features + categorical_features]
    y_cad = df["avg_cadence"]
    y_spd = df["avg_speed"]

    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="mean")),
            ("scaler", StandardScaler())
        ]), numeric_features),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]), categorical_features)
    ])

    # Complete pipeline
    pipeline_cad = Pipeline([
        ("preprocessor", preprocessor),
        ("model", GradientBoostingRegressor(random_state=42))
    ])

    pipeline_spd = Pipeline([
        ("preprocessor", preprocessor),
        ("model", GradientBoostingRegressor( random_state=42))
    ])

    # Train model
    pipeline_cad.fit(X, y_cad)
    pipeline_spd.fit(X, y_spd)

    # Get model paths
    model_cad_path, model_spd_path = get_model_paths(user_id)
    # Save the models
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

    X = preprocess_segments_for_prediction(df)

    if "speed_model" in models:
        df["avg_speed"] = models["speed_model"].predict(X)
    else:
        df["avg_speed"] = np.nan

    if "cadence_model" in models:
        df["avg_cadence"] = models["cadence_model"].predict(X)
    else:
        df["avg_cadence"] = np.nan

    # Compute the estimated time and update start_time / end_time
    df["estimated_time"] = df["segment_length"] / df["avg_speed"].replace(0, np.nan)
    df["start_time"] = np.cumsum([0] + df["estimated_time"].iloc[:-1].tolist())
    df["end_time"] = df["start_time"] + df["estimated_time"]

    # Insert in segments only the updated columns
    update_cols = ["segment_id", "avg_speed", "avg_cadence", "start_time", "end_time"]
    update_segment_predictions(activity_id, df[update_cols], engine)
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