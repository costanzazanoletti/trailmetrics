import logging
import logging_setup
import threading
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import pairwise_distances
from database import (
    engine, 
    get_activity_status_fingerprint, 
    get_similarity_status_fingerprint, 
    update_similarity_status_fingerprint,
    get_user_segments,
    delete_user_similarity_data,
    save_similarity_data,
    update_similarity_status_in_progress
)

logger = logging.getLogger("app")

def preprocess_data(df_segment, numeric_features, categorical_features):
    """Pre-process the data with scaling for numeric features and one-hot encoding for categorical features"""
    # Define the preprocessor pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(), categorical_features)
        ],
        remainder='drop'  # Drop any other columns not specified
    )
    # Create the full pipeline
    pipeline = Pipeline(steps=[('preprocessor', preprocessor)])

    # Extract features and apply pre-processing
    X = df_segment.drop(columns=['segment_id', 'grade_category'])
    X_processed = pipeline.fit_transform(X)

    return X_processed, pipeline

def compute_similarity(X_grade_category):
    """Compute the similarity matrix for the segments of the same grade category"""
    similarity_matrix = pairwise_distances(X_grade_category, metric='euclidean')
    return similarity_matrix

def compute_similarity_matrix(df):
    """Compute similarity within segments of the same grade category"""
    segment_features = [
        'segment_length',        
        'start_distance',       
        'start_time',           
        'start_altitude',       
        'elevation_gain',       
        'avg_gradient',    
        'road_type',       
        'surface_type',      
        'temperature',         
        'humidity',             
        'wind',              
        'weather_id'
    ]
    df_segment = df[segment_features + ['segment_id', 'grade_category']].copy()
    
    # Features that need to be pre-processed
    numeric_features = ['segment_length', 'start_distance', 'start_time', 'start_altitude', 
                        'elevation_gain', 'avg_gradient', 'temperature', 'humidity', 'wind']
    categorical_features = ['road_type', 'surface_type', 'weather_id']

    # Pre-process the data
    X_processed, pipeline = preprocess_data(df_segment, numeric_features, categorical_features)

    # Dictionary with grade_category as key and similarity_matrix as value
    similarity_matrices = {}

    # Iterate over the grade categories and calculate the similarity matrix for each one
    for grade_category in df_segment['grade_category'].unique():
        # Filter by grade_category
        mask = (df_segment['grade_category'] == grade_category).to_numpy()
        
        # Filter the pre-processed features
        X_grade_category = X_processed[mask]
        
        # Verify if there is more than one segment in this category
        if X_grade_category.shape[0] > 1:
            # Compute the similarity matrix
            similarity_matrix = compute_similarity(X_grade_category)
            similarity_matrices[grade_category] = similarity_matrix
        else:
            logger.warning(f"Grade Category {grade_category} has only one segment and is not processed.")
    
    return merge_similarity_matrices_with_original_df(similarity_matrices, df)

def merge_similarity_matrices_with_original_df(similarity_matrices, df):
    all_similarity_data = []
    for grade_category, similarity_matrix in similarity_matrices.items():
        segments_in_category = df[df['grade_category'] == grade_category]['segment_id'].tolist()  
        num_segments = len(segments_in_category)
        for i in range(num_segments):
            for j in range(i + 1, num_segments):  # Avoid duplicates and self-similarity
                segment_id_1 = segments_in_category[i]
                segment_id_2 = segments_in_category[j]
                similarity_score = similarity_matrix[i, j]
                all_similarity_data.append({
                    'segment_id_1': segment_id_1,
                    'segment_id_2': segment_id_2,
                    'similarity_score': similarity_score
                })
    return all_similarity_data

def run_similarity_computation(user_id):
    try:
        with engine.begin() as connection:
            # Get user's segments from database
            user_segments_df = get_user_segments(connection, user_id)
            if not user_segments_df.empty:
                logger.info(f"Computing similarity matrix for user {user_id} with {len(user_segments_df)} segments,")
                # Call compute_similarity_matrix
                similarity_data = compute_similarity_matrix(user_segments_df)
                logger.info(f"Similarity matrix for user {user_id} successfully computed.")
                # Clean old data and save new similarity_matrix
                delete_user_similarity_data(connection, user_id)
                save_similarity_data(connection, similarity_data)
            else:
                logger.info(f"No segments for user {user_id} to compute similarity matrix.")
    except Exception as e:
        logger.error(f"Similarity computation failed for user {user_id}: {e}.")
    finally:
        update_similarity_status_in_progress(engine, user_id, False)

def should_compute_similarity_for_user(engine, user_id):
    """
    Check and possibly trigger similarity computation for a user, if:
    - the total user activities match with the completed activities 
    - there is not a similarity matrix yet or there is one with a different fingerprint
    - the similarity computation is not currently in progress
    """
    try:
        with engine.begin() as connection:
            current_status = get_activity_status_fingerprint(connection, user_id)
            stored_fingerprint = get_similarity_status_fingerprint(connection, user_id)

            if not current_status:
                logger.info(f"Should not compute similarity matrix for user {user_id}. No activity status.")
                return False

            total, completed, current_fp = current_status
            if total == 0 or total != completed:
                logger.info(f"Should not compute similarity matrix for user {user_id}. Total activities: {total}, completed {completed}.")
                return False

            if stored_fingerprint:
                stored_fp, in_progress = stored_fingerprint
                if current_fp == stored_fp or in_progress:
                    logger.info(f"Should not compute similarity matrix for user {user_id}. Activities not changed or already in progress.")
                    return False

            # At this point, we are good to trigger computation
            logger.info(f"Start computing similarity matrix for user {user_id}")
            # Update DB to mark computation as in progress
            update_similarity_status_fingerprint(connection, user_id, current_fp)
             # Launch background thread for similarity computation
            thread = threading.Thread(
                target=run_similarity_computation,
                args=(user_id,),
                daemon=True
            )
            thread.start()

            return True
        
    except Exception as e:
        raise RuntimeError(f"Error checking similarity computation need for user {user_id}: {e}")