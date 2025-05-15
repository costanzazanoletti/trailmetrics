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
from utils.percentiles import map_percentile_to_zone

logger = logging.getLogger("app")

def calculate_efficiency_zones_for_segments(engine, segment_ids=None, force=False):
    with engine.begin() as connection:
        df = fetch_efficiency_zone_input_df(connection, segment_ids)
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
                logger.info(f"Prepared efficiency zones {zone_sim} {zone_grade} for segment {row.segment_id}")

            except Exception as e:
                logger.warning(f"Failed to process segment {row.segment_id}: {e}")

        if records:
            insert_segment_efficiency_zones_batch(connection, records)
            logger.info(f"Inserted {len(records)} efficiency zones in batch")
