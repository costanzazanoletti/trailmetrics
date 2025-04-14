import logging
import logging_setup
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import pairwise_distances

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
