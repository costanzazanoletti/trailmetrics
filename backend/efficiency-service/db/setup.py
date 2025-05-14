import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
               f"{os.getenv('POSTGRES_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"

# Override per testing
if "pytest" in sys.modules:
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", DATABASE_URL)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)
