import logging
import logging_setup
import threading
import pandas as pd
import numpy as np
import os
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from db.setup import engine
from db.segments import get_user_segments
from db.similarity import (
    delete_user_similarity_data,
    save_similarity_data,
    get_activity_status_fingerprint, 
    get_similarity_status_fingerprint, 
    update_similarity_status_fingerprint,
    update_similarity_status_in_progress,
    mark_similarity_processed_for_user
)
from utils.terrain import group_highway_for_analysis, group_surface_for_analysis
# Init logger
logger = logging.getLogger("app")
# Get environment variables
load_dotenv()

TOP_K_SIMILAR_SEGMENTS = int(os.getenv("TOP_K_SIMILAR_SEGMENTS", "10"))
SIMILARITY_COMPUTATION_METHOD = os.getenv("SIMILARITY_COMPUTATION_METHOD", "euclidean") # 'euclidean' or 'cosine'
   
def preprocess_data_by_grade(df_segment, numeric_features, original_categorical_features, n_components_pca=None):
    """Pre-process data (handle missing, group, scale, encode, PCA) within each grade category, using only specified features."""
    df = df_segment.copy()

    # Handle missing surface values and group highway/surface
    df['grouped_highway'] = df['road_type'].apply(group_highway_for_analysis)
    df['grouped_surface'] = df.apply(lambda row: group_surface_for_analysis(row['surface_type'], row['road_type']), axis=1)

    # Define final categorical features after grouping
    final_categorical_features = ['grouped_highway', 'grouped_surface'] + [col for col in original_categorical_features if col not in ['road_type', 'surface_type']]

    # Select all features to be processed
    features_to_process = numeric_features + final_categorical_features

    # Preprocessor pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='mean')),
                ('scaler', StandardScaler())
            ]), numeric_features),
            ('cat', Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(handle_unknown='ignore'))
            ]), final_categorical_features)
        ],
        remainder='drop'  # Drop any columns not specified in transformers
    )

    # Apply preprocessing
    processed_data = preprocessor.fit_transform(df[features_to_process])

    # Get feature names after one-hot encoding
    feature_names = preprocessor.get_feature_names_out()

    processed_df = pd.DataFrame(processed_data, columns=feature_names)

    # Apply PCA if n_components is specified and conditions are met
    if n_components_pca is not None and n_components_pca > 0:
        pca_features = processed_df.columns  # PCA on all processed features
        n_features = len(pca_features)
        n_samples = processed_df.shape[0]

        if n_components_pca < min(n_samples, n_features):
            logger.info(f"Applying PCA with {n_components_pca} components (Grade: {df_segment['grade_category'].iloc[0]})")
            pca = PCA(n_components=n_components_pca)
            principal_components = pca.fit_transform(processed_df[pca_features])
            pca_df = pd.DataFrame(data=principal_components,
                                  columns=[f'principal_component_{i+1}' for i in range(n_components_pca)])
            processed_df = pca_df
        else:
            logger.warning(f"n_components_pca={n_components_pca} is invalid for PCA (Grade: {df_segment['grade_category'].iloc[0]}, Samples: {n_samples}, Features: {n_features}). Skipping PCA.")

    # Add back segment_id and grade_category
    processed_df['segment_id'] = df['segment_id'].values
    processed_df['grade_category'] = df['grade_category'].values

    return processed_df

def get_top_k_similar_segments(similarity_matrices, k=5, method='euclidean'):
    """Finds the top-k most similar segments for each segment within each grade category."""
    top_k_data = []
    for grade_category, (similarity_matrix, segment_ids) in similarity_matrices.items():
        num_segments = len(segment_ids)
        for i in range(num_segments):
            reference_segment_id = segment_ids[i]
            similarity_scores = similarity_matrix[i]

            # Sort by similarity (descending for cosine, ascending for euclidean)
            if method == 'cosine':
                sorted_indices = np.argsort(similarity_scores)[::-1]
            else:  # euclidean
                sorted_indices = np.argsort(similarity_scores)

            top_k_similar = []
            count = 0
            for idx in sorted_indices:
                similar_segment_id = segment_ids[idx]
                if similar_segment_id != reference_segment_id:
                    top_k_similar.append({
                        'similar_segment_id': similar_segment_id,
                        'similarity_score': similarity_scores[idx]
                    })
                    count += 1
                    if count >= k:
                        break

            for rank, similar_segment in enumerate(top_k_similar):
                top_k_data.append({
                    'segment_id': reference_segment_id,
                    'similar_segment_id': similar_segment['similar_segment_id'],
                    'similarity_score': similar_segment['similarity_score'],
                    'rank': rank + 1
                })
    return pd.DataFrame(top_k_data)

def compute_similarity_matrix_by_grade(df, method, numeric_features, original_categorical_features, n_components_pca=None):
    """Compute similarity within segments of the same grade category after preprocessing (grouping, scaling, encoding, PCA)."""
    similarity_matrices = {}

    for grade_category in df['grade_category'].unique():
        df_grade = df[df['grade_category'] == grade_category].copy()
        logger.info(f"Computing {method} similarity for grade category {grade_category}")

        if len(df_grade) > 1:
            processed_df_grade = preprocess_data_by_grade(df_grade, numeric_features, original_categorical_features, n_components_pca)

            features_for_similarity = [col for col in processed_df_grade.columns if col.startswith('principal_component_') or col.startswith('num__') or col.startswith('cat__')]

            if features_for_similarity:
                X_grade_category = processed_df_grade[features_for_similarity].values

                if method == 'euclidean':
                    similarity_matrix = pairwise_distances(X_grade_category, metric='euclidean')
                else:
                    similarity_matrix = cosine_similarity(X_grade_category)
                                
                similarity_matrices[grade_category] = (similarity_matrix, df_grade['segment_id'].tolist())
                
            else:
                logger.warning(f"No features available for similarity calculation in Grade Category {grade_category}.")

        else:
            logger.info(f"Grade Category {grade_category} has only one segment and is not processed.")
    return similarity_matrices

def compute_similarity_matrix(df):
    """Compute similarity within segments of the same grade category"""
    # Features selected for similarity
    numeric_features = ['segment_length', 'start_distance', 'start_time', 'start_altitude',
                    'avg_gradient', 'temperature', 'humidity', 'wind', 
                    'cumulative_ascent', 'cumulative_descent']
    original_categorical_features = ['road_type', 'surface_type', 'weather_id']   

    # Preprocess and compute similarity within segments of the same grade category
    similarity_matrices_by_grade = compute_similarity_matrix_by_grade(
        df.copy(),  # Pass a copy to avoid modifying the original DataFrame
        method='euclidean',
        numeric_features=numeric_features,
        original_categorical_features=original_categorical_features,
        n_components_pca=10
    )
    # Get the top-k most similar segments
    top_k_similar_df = get_top_k_similar_segments(similarity_matrices_by_grade, k=TOP_K_SIMILAR_SEGMENTS, method=SIMILARITY_COMPUTATION_METHOD)
    logger.info(f"Computed {len(top_k_similar_df)} segment top-{TOP_K_SIMILAR_SEGMENTS} similarities with {SIMILARITY_COMPUTATION_METHOD} method")
    return top_k_similar_df

def run_similarity_computation(user_id):
    """Run the full similarity computation pipeline for a user: 
    - fetch segments,
    - compute similarity,
    - clean old data,
    - save new data,
    - update status."""
    
    connection = engine.connect()
    trans = connection.begin() # Manually start the transaction

    try:
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

        trans.commit() # Manually commit the transaction
        # Update user's activities status after the pipeline is closed
        mark_similarity_processed_for_user(engine, user_id)
    except Exception as e:
        logger.error(f"Similarity computation failed for user {user_id}: {e}.")
        trans.rollback() # Manually rollback if an exception is raised
    finally:
        connection.close() # Close the connection
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
        
        # Launch background thread for similarity computation outside the transaction
        thread = threading.Thread(
            target=run_similarity_computation,
            args=(user_id,),
            daemon=True
        )
        thread.start()

        return True
        
    except Exception as e:
        raise RuntimeError(f"Error checking similarity computation need for user {user_id}: {e}")