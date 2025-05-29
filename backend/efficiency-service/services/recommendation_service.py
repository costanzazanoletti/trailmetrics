import logging
import logging_setup
import joblib
import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from db.recommendation import fetch_user_zone_segments
from utils.terrain import group_highway_for_analysis, group_surface_for_analysis 

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

    # Save
    os.makedirs("models", exist_ok=True)
    joblib.dump(pipeline_cad, f"models/model_cad_user_{user_id}.pkl")
    joblib.dump(pipeline_spd, f"models/model_spd_user_{user_id}.pkl")
    logger.info(f"Saved models for user {user_id}")