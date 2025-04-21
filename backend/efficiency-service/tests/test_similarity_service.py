import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from app.similarity_service import (
    group_highway_for_analysis,
    group_surface_for_analysis,
    preprocess_data_by_grade, 
    compute_similarity_matrix_by_grade, 
    get_top_k_similar_segments,
    compute_similarity_matrix,
    should_compute_similarity_for_user,
    run_similarity_computation
    )

@patch('app.similarity_service.run_similarity_computation')
@patch('app.similarity_service.update_similarity_status_fingerprint')
@patch('app.similarity_service.get_similarity_status_fingerprint')
@patch('app.similarity_service.get_activity_status_fingerprint')
def test_should_compute_similarity_for_user(
    mock_get_activity_status_fingerprint,
    mock_get_similarity_status_fingerprint,
    mock_update_similarity_status_fingerprint,
    mock_run_similarity_computation,
    mock_engine
):
    """Test should_compute_similarity_for_user returns True for a user with different fingerprints"""
    # Mock the return values
    mock_get_activity_status_fingerprint.return_value = (5, 5, 'fp1')
    mock_get_similarity_status_fingerprint.return_value = ('fp2', False)

    # Call the function
    user_id = 123
    result = should_compute_similarity_for_user(mock_engine, user_id=user_id)

    assert result is True
    mock_update_similarity_status_fingerprint.assert_called_once()
    mock_run_similarity_computation.assert_called_once_with(user_id)

@patch('app.similarity_service.run_similarity_computation')
@patch('app.similarity_service.update_similarity_status_fingerprint')
@patch('app.similarity_service.get_similarity_status_fingerprint')
@patch('app.similarity_service.get_activity_status_fingerprint')
def test_should_not_compute_similarity_if_no_activities(
    mock_get_activity_status_fingerprint,
    mock_get_similarity_status_fingerprint,
    mock_update_similarity_status_fingerprint,
    mock_run_similarity_computation,
    mock_engine
):
    """Test should_compute_similarity_for_user should return True for a user that has no activity status fingerprint"""
    # Mock the return values
    mock_get_activity_status_fingerprint.return_value = (0, 0, None)
    mock_get_similarity_status_fingerprint.return_value = ('fp2', False)

    # Call the function
    user_id = 123
    result = should_compute_similarity_for_user(mock_engine, user_id=user_id)

    assert result is False
    mock_update_similarity_status_fingerprint.assert_not_called()
    mock_run_similarity_computation.assert_not_called()

@patch('app.similarity_service.run_similarity_computation')
@patch('app.similarity_service.update_similarity_status_fingerprint')
@patch('app.similarity_service.get_similarity_status_fingerprint')
@patch('app.similarity_service.get_activity_status_fingerprint')
def test_should_not_compute_similarity_if_same_fingerprint(
    mock_get_activity_status_fingerprint,
    mock_get_similarity_status_fingerprint,
    mock_update_similarity_status_fingerprint,
    mock_run_similarity_computation,
    mock_engine
):
    """Test should_compute_similarity_for_user should return False for a user with identical fingerprints"""
    # Mock the return values
    mock_get_activity_status_fingerprint.return_value = (10, 10, 'fp1')
    mock_get_similarity_status_fingerprint.return_value = ('fp1', False)

    # Call the function
    user_id = 123
    result = should_compute_similarity_for_user(mock_engine, user_id=user_id)

    assert result is False
    mock_update_similarity_status_fingerprint.assert_not_called()
    mock_run_similarity_computation.assert_not_called()

@patch('app.similarity_service.run_similarity_computation')
@patch('app.similarity_service.update_similarity_status_fingerprint')
@patch('app.similarity_service.get_similarity_status_fingerprint')
@patch('app.similarity_service.get_activity_status_fingerprint')
def test_should_not_compute_similarity_if_in_progress(
    mock_get_activity_status_fingerprint,
    mock_get_similarity_status_fingerprint,
    mock_update_similarity_status_fingerprint,
    mock_run_similarity_computation,
    mock_engine
):
    """Test should_compute_similarity_for_user should return False for a user that in progess similarity computation"""
    # Mock the return values
    mock_get_activity_status_fingerprint.return_value = (10, 10, 'fp2')
    mock_get_similarity_status_fingerprint.return_value = ('fp1', True)

    # Call the function
    user_id = 123
    result = should_compute_similarity_for_user(mock_engine, user_id=user_id)

    assert result is False
    mock_update_similarity_status_fingerprint.assert_not_called()
    mock_run_similarity_computation.assert_not_called()

def test_group_highway_for_analysis():
    """Test group_highway_for_analysis with different values"""
    assert group_highway_for_analysis(None) == 'unspecified_road'
    assert group_highway_for_analysis('steps') == 'steps'
    assert group_highway_for_analysis('path') == 'pedestrian_cycle'
    assert group_highway_for_analysis('track') == 'minor_road'
    assert group_highway_for_analysis('secondary') == 'major_road'
    assert group_highway_for_analysis('unknown') == 'other_road'

def test_group_surface_for_analysis():
    """Test group_surface_for_analysis with different values"""
    assert group_surface_for_analysis(None, 'path') == 'unpaved'
    assert group_surface_for_analysis(None, 'cycleway') == 'paved'
    assert group_surface_for_analysis('asphalt', 'residential') == 'paved'
    assert group_surface_for_analysis('gravel', 'track') == 'unpaved'
    assert group_surface_for_analysis('grass', 'footway') == 'soft'
    assert group_surface_for_analysis('rock', 'steps') == 'rocky'
    assert group_surface_for_analysis('other', 'trunk') == 'other_surface'

def test_preprocess_data_by_grade():
    """Test preprocess_data_by_grade with different sample size that trigger or not PCA computation"""
    data_few = {'segment_id': ['seg1', 'seg2'],
                'grade_category': [1.0, 1.25],
                'segment_length': [100, 200],
                'road_type': ['path', None],
                'surface_type': ['gravel', 'asphalt'],
                'start_distance': [0, 100],
                'start_time': [1, 2],
                'start_altitude': [10, 20],
                'elevation_gain': [5, 10],
                'avg_gradient': [0.05, 0.1],
                'temperature': [20, 25],
                'humidity': [60, 70],
                'wind': [5, 10],
                'weather_id': [800, 801]}
    df_few = pd.DataFrame(data_few)
    numeric_features = ['segment_length', 'start_distance', 'start_time', 'start_altitude', 'elevation_gain', 'avg_gradient', 'temperature', 'humidity', 'wind']
    original_categorical_features = ['road_type', 'surface_type', 'weather_id']
    processed_df_few = preprocess_data_by_grade(df_few, numeric_features, original_categorical_features, n_components_pca=2)
    # PCA should NOT be applied with 2 samples and 11 features
    assert 'principal_component_1' not in processed_df_few.columns
    assert 'num__segment_length' in processed_df_few.columns
    assert 'cat__grouped_highway_pedestrian_cycle' in processed_df_few.columns
    assert processed_df_few.shape[1] > 2 # Should still have original processed features

    data_many = {'segment_id': ['seg1', 'seg2', 'seg3'],
                 'grade_category': [1.0, 1.25, 1.0],
                 'segment_length': [100, 200, 150],
                 'road_type': ['path', None, 'track'],
                 'surface_type': ['gravel', 'asphalt', 'unpaved'],
                 'start_distance': [0, 100, 50],
                 'start_time': [1, 2, 3],
                 'start_altitude': [10, 20, 15],
                 'elevation_gain': [5, 10, 7],
                 'avg_gradient': [0.05, 0.1, 0.08],
                 'temperature': [20, 25, 22],
                 'humidity': [60, 70, 65],
                 'wind': [5, 10, 7],
                 'weather_id': [800, 801, 802]}
    df_many = pd.DataFrame(data_many)
    processed_df_pca_many = preprocess_data_by_grade(df_many, numeric_features, original_categorical_features, n_components_pca=2)
    # PCA SHOULD be applied with 3 samples and 11 features (2 < min(3, 11))
    assert 'principal_component_1' in processed_df_pca_many.columns
    assert 'principal_component_2' in processed_df_pca_many.columns
    assert 'num__segment_length' not in processed_df_pca_many.columns
    assert 'cat__grouped_highway_pedestrian_cycle' not in processed_df_pca_many.columns
    assert 'segment_id' in processed_df_pca_many.columns
    assert 'grade_category' in processed_df_pca_many.columns

    data = {'segment_id': ['seg1', 'seg2'],
            'grade_category': [1.0, 1.25],
            'segment_length': [100, 200],
            'road_type': ['path', None],
            'surface_type': ['gravel', 'asphalt'],
            'start_distance': [0, 100],
            'start_time': [1, 2],
            'start_altitude': [10, 20],
            'elevation_gain': [5, 10],
            'avg_gradient': [0.05, 0.1],
            'temperature': [20, 25],
            'humidity': [60, 70],
            'wind': [5, 10],
            'weather_id': [800, 801]}
    df = pd.DataFrame(data)
    processed_df = preprocess_data_by_grade(df, numeric_features, original_categorical_features)
    assert 'num__segment_length' in processed_df.columns
    assert 'cat__grouped_highway_pedestrian_cycle' in processed_df.columns
    assert 'segment_id' in processed_df.columns
    assert 'grade_category' in processed_df.columns
    assert processed_df.shape[0] == 2
    assert processed_df['segment_id'].dtype == object  # String type
    assert processed_df['grade_category'].dtype == float

def test_compute_similarity_matrix_by_grade():
    """Test compute_similarity_matrix_by_grade with cosine and euclidean method"""
    data = {'segment_id': ['seg1', 'seg2', 'seg3', 'seg4'],
            'grade_category': [1.0, 1.0, 1.25, 1.25],
            'segment_length': [100, 200, 150, 250],
            'road_type': ['path', None, 'track', 'residential'],
            'surface_type': ['gravel', 'asphalt', 'unpaved', 'paved'],
            'start_distance': [0, 100, 50, 150],
            'start_time': [1, 2, 3, 4],
            'start_altitude': [10, 20, 15, 25],
            'elevation_gain': [5, 10, 7, 12],
            'avg_gradient': [0.05, 0.1, 0.08, 0.12],
            'temperature': [20, 25, 22, 28],
            'humidity': [60, 70, 65, 75],
            'wind': [5, 10, 7, 12],
            'weather_id': [800, 801, 802, 803]}
    df = pd.DataFrame(data)
    numeric_features = ['segment_length', 'start_distance', 'start_time', 'start_altitude', 'elevation_gain', 'avg_gradient', 'temperature', 'humidity', 'wind']
    original_categorical_features = ['road_type', 'surface_type', 'weather_id']
    similarity_matrices = compute_similarity_matrix_by_grade(df, 'euclidean', numeric_features, original_categorical_features, n_components_pca=2)
        
    assert 1.0 in similarity_matrices
    assert 1.25 in similarity_matrices
    assert len(similarity_matrices[1.0][0]) == 2
    assert len(similarity_matrices[1.25][0]) == 2
    assert len(similarity_matrices[1.0][1]) == 2
    assert len(similarity_matrices[1.25][1]) == 2
    assert all(isinstance(seg_id, str) for seg_id in similarity_matrices[1.0][1])
    assert all(isinstance(grade, float) and grade % 0.25 == 0 for grade in df['grade_category'].unique())

    similarity_matrices_pca = compute_similarity_matrix_by_grade(df, 'cosine', numeric_features, original_categorical_features, n_components_pca=2)
    assert 1.0 in similarity_matrices_pca
    assert 1.25 in similarity_matrices_pca

def test_get_top_k_similar_segments():
    """Test get_top_k_similar_segments of similarity matrices computed with cosine and euclidean method"""
    similarity_matrices = {
        1.0: (np.array([[0, 0.1, 0.2], [0.1, 0, 0.05], [0.2, 0.05, 0]]), ['seg1', 'seg2', 'seg3']),
        1.5: (np.array([[0, 0.5], [0.5, 0]]), ['seg4', 'seg5'])
    }
    df_segments = pd.DataFrame({'segment_id': ['seg1', 'seg2', 'seg3', 'seg4', 'seg5'], 'grade_category': [1.0, 1.0, 1.0, 1.5, 1.5]})
    top_k_df = get_top_k_similar_segments(similarity_matrices, k=1, method='euclidean')
    assert top_k_df.shape[0] == 5
    for seg_id in ['seg1', 'seg2', 'seg3', 'seg4', 'seg5']:
        assert top_k_df[top_k_df['segment_id'] == seg_id].shape[0] == 1
        assert isinstance(top_k_df[top_k_df['segment_id'] == seg_id]['segment_id'].iloc[0], str)

    top_k_df_cosine = get_top_k_similar_segments(similarity_matrices, k=2, method='cosine')
    assert top_k_df_cosine.shape[0] == 8
    assert all(isinstance(seg_id, str) for seg_id in top_k_df_cosine['segment_id'].unique())

def test_compute_similarity_matrix():

    data = {'segment_id': ['seg1', 'seg2', 'seg3', 'seg4'],
            'grade_category': [1.0, 1.0, 1.25, 1.25],
            'segment_length': [100, 200, 150, 250],
            'road_type': ['path', None, 'track', 'residential'],
            'surface_type': ['gravel', 'asphalt', 'unpaved', 'paved'],
            'start_distance': [0, 100, 50, 150],
            'start_time': [1, 2, 3, 4],
            'start_altitude': [10, 20, 15, 25],
            'elevation_gain': [5, 10, 7, 12],
            'avg_gradient': [0.05, 0.1, 0.08, 0.12],
            'temperature': [20, 25, 22, 28],
            'humidity': [60, 70, 65, 75],
            'wind': [5, 10, 7, 12],
            'weather_id': [800, 801, 802, 803]}
    df = pd.DataFrame(data)
    top_k_df = compute_similarity_matrix(df)
    assert top_k_df.shape[0] == 4
    assert all(isinstance(seg_id, str) for seg_id in top_k_df['segment_id'].unique())
    assert all(isinstance(similar_seg_id, str) for similar_seg_id in top_k_df['similar_segment_id'].unique())
    assert 'similarity_score' in top_k_df.columns
    assert 'rank' in top_k_df.columns

@patch("app.similarity_service.engine")
@patch("app.similarity_service.update_similarity_status_in_progress")
@patch("app.similarity_service.save_similarity_data")
@patch("app.similarity_service.delete_user_similarity_data")
@patch("app.similarity_service.compute_similarity_matrix")
@patch("app.similarity_service.get_user_segments")
def test_run_similarity_computation_with_segments(
    mock_get_user_segments,
    mock_compute_similarity_matrix,
    mock_delete_user_similarity_data,
    mock_save_similarity_data,
    mock_update_similarity_status,
    mock_engine
):
    mock_connection = MagicMock()
    mock_engine.connect.return_value = mock_connection
    mock_transaction = MagicMock()
    mock_connection.begin.return_value = mock_transaction

    mock_get_user_segments.return_value = pd.DataFrame([
        {"segment_id": "seg1", "grade_category": 1.5},
        {"segment_id": "seg2", "grade_category": 1.5},
        {"segment_id": "seg3", "grade_category": 2.0},
        {"segment_id": "seg4", "grade_category": 2.0},
    ])
    mock_compute_similarity_matrix.return_value = pd.DataFrame([
        {"segment_id": "seg1", "similar_segment_id": "seg2", "similarity_score": 0.9, "rank": 1}
    ])

    user_id = 42
    run_similarity_computation(user_id)

    mock_get_user_segments.assert_called_once_with(mock_connection, user_id)
    mock_compute_similarity_matrix.assert_called_once()
    mock_delete_user_similarity_data.assert_called_once_with(mock_connection, user_id)
    mock_save_similarity_data.assert_called_once_with(mock_connection, mock_compute_similarity_matrix.return_value)
    mock_update_similarity_status.assert_called_once_with(mock_engine, user_id, False)
    mock_transaction.commit.assert_called_once()
    mock_connection.close.assert_called_once()

@patch("app.similarity_service.engine")
@patch("app.similarity_service.update_similarity_status_in_progress")
@patch("app.similarity_service.save_similarity_data")
@patch("app.similarity_service.delete_user_similarity_data")
@patch("app.similarity_service.compute_similarity_matrix")
@patch("app.similarity_service.get_user_segments")
def test_run_similarity_computation_no_segments(
    mock_get_user_segments,
    mock_compute_similarity_matrix,
    mock_delete_user_similarity_data,
    mock_save_similarity_data,
    mock_update_similarity_status,
    mock_engine
):
    mock_connection = MagicMock()
    mock_engine.connect.return_value = mock_connection
    mock_transaction = MagicMock()
    mock_connection.begin.return_value = mock_transaction

    mock_get_user_segments.return_value = pd.DataFrame()

    user_id = 101
    run_similarity_computation(user_id)

    mock_get_user_segments.assert_called_once_with(mock_connection, user_id)
    mock_compute_similarity_matrix.assert_not_called()
    mock_delete_user_similarity_data.assert_not_called()
    mock_save_similarity_data.assert_not_called()
    mock_update_similarity_status.assert_called_once_with(mock_engine, user_id, False)
    mock_transaction.commit.assert_called_once()
    mock_connection.close.assert_called_once()

@patch("app.similarity_service.engine")
@patch("app.similarity_service.update_similarity_status_in_progress")
@patch("app.similarity_service.save_similarity_data")
@patch("app.similarity_service.delete_user_similarity_data")
@patch("app.similarity_service.compute_similarity_matrix")
@patch("app.similarity_service.get_user_segments")
def test_run_similarity_computation_exception(
    mock_get_user_segments,
    mock_compute_similarity_matrix,
    mock_delete_user_similarity_data,
    mock_save_similarity_data,
    mock_update_similarity_status,
    mock_engine
):
    mock_connection = MagicMock()
    mock_engine.connect.return_value = mock_connection
    mock_transaction = MagicMock()
    mock_connection.begin.return_value = mock_transaction

    mock_get_user_segments.return_value = pd.DataFrame([
        {"segment_id": "seg1", "grade_category": 1.5},
        {"segment_id": "seg2", "grade_category": 1.5},
    ])
    mock_compute_similarity_matrix.side_effect = Exception("Similarity computation failed")

    user_id = 200
    run_similarity_computation(user_id)

    mock_get_user_segments.assert_called_once_with(mock_connection, user_id)
    mock_compute_similarity_matrix.assert_called_once()
    mock_delete_user_similarity_data.assert_not_called() # Rollback should prevent these
    mock_save_similarity_data.assert_not_called()
    mock_transaction.rollback.assert_called_once()
    mock_connection.close.assert_called_once()
    mock_update_similarity_status.assert_called_once_with(mock_engine, user_id, False)