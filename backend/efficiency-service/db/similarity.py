import logging
import logging_setup
import pandas as pd
from sqlalchemy import text
from exceptions.exceptions import DatabaseException
from sqlalchemy.exc import SQLAlchemyError
from db.setup import engine
from db.core import execute_sql, fetch_one_sql, fetch_all_sql_df

logger = logging.getLogger("app")

def chunked(iterable, size=5000):
    """Yield successive chunks from iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

def save_similarity_data(connection, similarity_data):
    """
    Bulk insert similarity data into the segment_similarity table in chunks.
    """
    if similarity_data.empty:
        logger.info("No similarity data to insert")
        return

    data_to_insert = []
    for index, row in similarity_data.iterrows():
        data_to_insert.append({
            'segment_id': row['segment_id'],
            'similar_segment_id': row['similar_segment_id'],
            'similarity_score': float(row['similarity_score']),
            'rank': int(row['rank'])
        })

    query = text("""
        INSERT INTO segment_similarity (
            segment_id, similar_segment_id, similarity_score, rank
        )
        VALUES (
            :segment_id, :similar_segment_id, :similarity_score, :rank
        )
        ON CONFLICT (segment_id, similar_segment_id) DO UPDATE 
        SET similarity_score = EXCLUDED.similarity_score,
            rank = EXCLUDED.rank,
            calculated_at = CURRENT_TIMESTAMP
    """)

    total_rows = 0
    for chunk in chunked(data_to_insert, size=5000):
        result = connection.execute(query, chunk)
        total_rows += result.rowcount
        logger.info(f"Inserted {total_rows} segment similarity rows.")

    logger.info(f"Saved similarity data: {total_rows} rows affected.")

def delete_user_similarity_data(connection, user_id):
    """
    Deletes similarity scores from the segment_similarity table
    where either segment_id or similar_segment_id belongs to the given user's segments.
    """
    query = """
            DELETE FROM segment_similarity
            WHERE segment_id IN (SELECT segment_id FROM segments WHERE user_id = :user_id)
            OR similar_segment_id IN (SELECT segment_id FROM segments WHERE user_id = :user_id)
    """
    result = execute_sql(connection, query, {"user_id": user_id})
    logger.info(f"Deleted similarity data: {result.rowcount} rows affected.")

def get_activity_status_fingerprint(connection, user_id):
    """Get activities and activitys status for a given user, with fingerprint."""
    query = """
                SELECT
                    COUNT(*) AS total_activities,
                    COUNT(*) FILTER (
                        WHERE 
                            (segment_status AND terrain_status AND weather_status)
                            OR not_processable
                    ) AS completed_activities,
                    md5(string_agg(activity_id::TEXT, ',' ORDER BY activity_id)) AS fingerprint
                FROM (
                    SELECT DISTINCT a.id AS activity_id, ast.segment_status, ast.terrain_status, ast.weather_status, ast.not_processable
                    FROM activities a
                    LEFT JOIN activity_status_tracker ast ON ast.activity_id = a.id
                    WHERE a.athlete_id = :user_id
                ) sub;
            """
    return fetch_one_sql(connection, query, {"user_id": user_id})

def get_similarity_status_fingerprint(connection, user_id):
    """Gets the similarity status fingerprint and the in progress state for the given user"""
    query = """
                SELECT activity_fingerprint, in_progress 
                FROM similarity_status_fingerprint 
                WHERE user_id = :user_id;
                """
    return fetch_one_sql(connection, query, {"user_id": user_id})

def update_similarity_status_fingerprint(connection, user_id, activity_fingerprint):
    query = """
        INSERT INTO similarity_status_fingerprint (user_id, in_progress, similarity_calculated_at, activity_fingerprint)
        VALUES (:user_id, true, now(), :fingerprint)
        ON CONFLICT (user_id) DO UPDATE
        SET in_progress = true,
            similarity_calculated_at = now(),
            activity_fingerprint = EXCLUDED.activity_fingerprint;
    """
    execute_sql(connection, query, {"user_id": user_id, "fingerprint": activity_fingerprint})

def update_similarity_status_in_progress(engine, user_id, in_progress):
    try:
        with engine.begin() as connection:
            query = """
                UPDATE similarity_status_fingerprint 
                SET in_progress = :in_progress
                WHERE user_id = :user_id
            """
            execute_sql(connection, query, {"user_id": user_id, "in_progress": in_progress})
            logger.info(f"Updated in_progress similarity status for user {user_id} to {in_progress}")
    except SQLAlchemyError as e:
        logger.error(f"Database error during similarity status update for user {user_id}: {e}")
        raise DatabaseException(f"Database error: {e}")
    
def mark_similarity_processed_for_user(engine, user_id):
    """Set similarity_processed_at = now() for all valid activities of the user."""
    query = """
        UPDATE activity_status_tracker
        SET similarity_processed_at = now()
        WHERE activity_id IN (
            SELECT ast.activity_id
            FROM activity_status_tracker ast
            JOIN activities a ON ast.activity_id = a.id
            WHERE a.athlete_id = :user_id AND ast.not_processable = false
        );
    """
    with engine.begin() as connection:
        execute_sql(connection, query, {"user_id": user_id})

