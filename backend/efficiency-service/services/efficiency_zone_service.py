import logging
import logging_setup
from datetime import datetime, timezone
from db.efficiency import (
    fetch_efficiency_zone_input_df,
    fetch_similar_efficiencies_df,
    fetch_grade_efficiencies_df, 
    insert_segment_efficiency_zones_batch
)
from db.core import execute_sql
from db.setup import engine
from utils.percentiles import map_percentile_to_zone

logger = logging.getLogger("app")

def calculate_efficiency_zones_for_segments(engine, segment_ids=None, force=False, limit=1000):
    with engine.begin() as connection:
        df = fetch_efficiency_zone_input_df(connection, segment_ids, limit=limit)

        if df.empty:
            logger.info("No segments need efficiency zone update")
            return 0

        logger.info(f"Processing {len(df)} segments for efficiency zone update")

        records = []
        for row in df.itertuples():
            try:
                if not force and not row.similarity_calculated_at:
                    continue

                if row.efficiency_score is None:
                    continue

                sim_df = fetch_similar_efficiencies_df(connection, row.segment_id)
                grade_df = fetch_grade_efficiencies_df(connection, row.grade_category, row.activity_id)

                zone_sim = map_percentile_to_zone(row.efficiency_score, sim_df["efficiency_score"].tolist())
                zone_grade = map_percentile_to_zone(row.efficiency_score, grade_df["efficiency_score"].tolist())

                records.append({
                    "segment_id": row.segment_id,
                    "zone_sim": zone_sim,
                    "zone_grade": zone_grade,
                    "calculated_at": datetime.now(timezone.utc),
                })

            except Exception as e:
                logger.warning(f"Failed to process segment {row.segment_id}: {e}")

        if records:
            insert_segment_efficiency_zones_batch(connection, records)
            logger.info(f"Inserted {len(records)} efficiency zones in batch")

        return len(records)

def run_efficiency_zone_batch():
    """
    Computes and updates efficiency zones for all the segments that require it. 
    It can be scheduled periodically.
    It processes segments paginated in windows of 1000 segments at a time
    """
    try:
        processed_total = 0 # counts processed segments
        while True:
            # Calculates zones for maximum 1000 segments
            count = calculate_efficiency_zones_for_segments(engine, limit=1000)
            
            if count == 0:
                break # If there are no more segments break the loop
            
            processed_total += count
        
        logger.info(f"Batch efficiency zone calculation completed. Segments updated: {processed_total}")
    except Exception as e:
        logger.exception(f"Failed to execute batch efficiency zone calculation: {e}")
