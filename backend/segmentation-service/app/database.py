# import os
# import sys
# import psycopg2
# import pandas as pd
# import numpy as np
# from sqlalchemy import create_engine, text
# from dotenv import load_dotenv

# # Load environment variables from .env
# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
# # If test mode use test database
# if "pytest" in sys.modules:
#     DATABASE_URL = os.getenv("TEST_DATABASE_URL", DATABASE_URL)

# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL is not set. Make sure the .env file exists and is configured correctly.")

# print(f"Database URL: {DATABASE_URL}")

# # Create a SQLAlchemy engine
# engine = create_engine(DATABASE_URL)

# def get_db_connection():
#     """Creates and returns a connection to PostgreSQL."""
#     return psycopg2.connect(DATABASE_URL)

# def get_raw_activity_streams(activity_id):
#     """
#     Retrieves raw time-series data for a given activity from the database.
#     """
#     query = """
#     SELECT type, data 
#     FROM activity_streams
#     WHERE activity_id = %s;
#     """
#     df_streams = pd.read_sql(query, engine, params=(activity_id,))
#     return df_streams

# def store_segments(segments_df):
#     """
#     Deletes existing segments for an activity and stores new segmented data into the 'segments' table.
#     """
#     if segments_df.empty:
#         print("No segments to store.")
#         return

#     conn = get_db_connection()
#     try:
#         cursor = conn.cursor()

#         # Begin transaction
#         conn.autocommit = False

#         # Convert DataFrame values to Python-native types
#         segments_df = segments_df.astype({
#             "activity_id": "int",
#             "start_distance": "float",
#             "end_distance": "float",
#             "segment_length": "float",
#             "avg_gradient": "float",
#             "avg_cadence": "float",
#             "grade_category": "float",
#             "start_lat": "float",
#             "start_lng": "float",
#             "end_lat": "float",
#             "end_lng": "float"
#         })

#         # Convert NumPy types to native Python types and handle NaN values
#         segments_df = segments_df.astype(object).where(pd.notnull(segments_df), None)
      
        
#         # Delete existing segments for the activity
#         delete_query = "DELETE FROM segments WHERE activity_id = %s;"
#         cursor.execute(delete_query, (segments_df.iloc[0]["activity_id"],))

#         # Insert new segments
#         insert_query = """
#         INSERT INTO segments (activity_id, start_distance, end_distance, segment_length, avg_gradient,
#                               avg_cadence, movement_type, type, grade_category,
#                               start_lat, start_lng, end_lat, end_lng)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """

#         for _, row in segments_df.iterrows():
#             cursor.execute(insert_query, (
#                 int(row["activity_id"]),
#                 float(row["start_distance"]),
#                 float(row["end_distance"]),
#                 float(row["segment_length"]),
#                 float(row["avg_gradient"]),
#                 float(row["avg_cadence"]),
#                 str(row["movement_type"]),
#                 str(row["type"]),
#                 float(row["grade_category"]),
#                 float(row["start_lat"]), 
#                 float(row["start_lng"]), 
#                 float(row["end_lat"]), 
#                 float(row["end_lng"])
#             ))

#         # Commit transaction
#         conn.commit()
#         print(f"Stored {len(segments_df)} segments in the database.")

#     except Exception as e:
#         conn.rollback()  # Rollback transaction in case of failure
#         print(f"Error storing segments: {e}")

#     finally:
#         cursor.close()
#         conn.close()


# def create_segments_table():
#     """
#     Checks if the 'segments' table exists. If not, creates it.
#     """
#     check_query = """
#     SELECT EXISTS (
#         SELECT FROM information_schema.tables 
#         WHERE table_name = 'segments'
#     );
#     """
    
#     create_query = """
#     CREATE TABLE segments (
#         id SERIAL PRIMARY KEY,
#         activity_id BIGINT NOT NULL,
#         start_distance FLOAT NOT NULL,
#         end_distance FLOAT NOT NULL,
#         segment_length FLOAT NOT NULL,
#         avg_gradient FLOAT NOT NULL,
#         avg_cadence FLOAT NOT NULL,
#         movement_type VARCHAR(20) NOT NULL,
#         type VARCHAR(20) NOT NULL,
#         grade_category FLOAT NOT NULL,
#         start_lat FLOAT NOT NULL,
#         end_lat FLOAT NOT NULL,
#         start_lng FLOAT NOT NULL,
#         end_lng FLOAT NOT NULL,
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     );
#     """
    
#     with engine.connect() as conn:
#         result = conn.execute(text(check_query))
#         table_exists = result.scalar()  # Returns True if the table exists, False otherwise

#         if not table_exists:
#             print("Table 'segments' not found. Creating it now...")
#             conn.execute(text(create_query))
#             conn.commit()
#             print("'segments' table created successfully.")
#         else:
#             print("Table 'segments' already exists. No action needed.")



# # Checks/creates the table on startup
# create_segments_table()