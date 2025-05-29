from db.core import fetch_all_sql_df, execute_sql_batch


def fetch_efficiency_zone_input_df(connection, segment_ids=None, limit: int=None):
    """
    Returns the segments that require efficiency zone calculation or update.
    It accepts a list of segment ids as optional parameter.
    It accepts a limit as optional parameter.
    """
    base_query = """
        SELECT s.segment_id, s.grade_category, s.activity_id, s.user_id,
        s.efficiency_score, z.calculated_at, ss.similarity_calculated_at
        FROM segments s
        JOIN activities a ON s.activity_id = a.id
        JOIN (
            SELECT segment_id, MAX(calculated_at) AS similarity_calculated_at
            FROM segment_similarity
            GROUP BY segment_id
        ) ss ON s.segment_id = ss.segment_id
        LEFT JOIN segment_efficiency_zone z ON s.segment_id = z.segment_id
        WHERE z.segment_id IS NULL OR ss.similarity_calculated_at > z.calculated_at
    """
    params = {}
    if segment_ids:
        base_query += " AND s.segment_id IN :segment_ids"
        params["segment_ids"] = segment_ids
    
    if limit:
        base_query += f" LIMIT {limit}"

    return fetch_all_sql_df(connection, base_query, params)


def fetch_similar_efficiencies_df(connection, segment_id):
    """
    Returns the efficiency_score of similar segments.
    """
    query = """
       SELECT efficiency_score
        FROM segments
        WHERE segment_id = :segment_id
           OR segment_id IN (
                SELECT segment_id
                FROM segment_similarity
                WHERE similar_segment_id = :segment_id
           )
           AND efficiency_score IS NOT NULL
    """
    return fetch_all_sql_df(connection, query, {"segment_id": segment_id})


def fetch_grade_efficiencies_df(connection, grade_category, activity_id):
    """
    Returns the efficiency_score of other segments with the same grade category.
    """
    query = """
        SELECT efficiency_score
        FROM segments
        WHERE grade_category = :grade_category
          AND efficiency_score IS NOT NULL
    """
    return fetch_all_sql_df(connection, query, {
        "grade_category": grade_category,
        "activity_id": activity_id
    })


def insert_segment_efficiency_zones_batch(connection, records: list[dict]):
    query = """
        INSERT INTO segment_efficiency_zone (segment_id, zone_among_similars, zone_among_grade_category, calculated_at)
        VALUES (:segment_id, :zone_sim, :zone_grade, :calculated_at)
        ON CONFLICT (segment_id) DO UPDATE
        SET zone_among_similars = EXCLUDED.zone_among_similars,
            zone_among_grade_category = EXCLUDED.zone_among_grade_category,
            calculated_at = EXCLUDED.calculated_at
    """
    return execute_sql_batch(connection, query, records)


 