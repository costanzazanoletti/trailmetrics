import pandas as pd
from sqlalchemy import text, bindparam
from app.exceptions import DatabaseException

def execute_sql(connection, query, params=None):
    """Helper function to execute SQL using SQLAlchemy with a provided connection.
    Automatically handles expanding bind parameters for lists (for use with IN clauses).
    """
    try:
        stmt = text(query)
        if params:
            for key, value in params.items():
                if isinstance(value, (list, tuple)):
                    stmt = stmt.bindparams(bindparam(key, expanding=True))
        return connection.execute(stmt, params)
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

def fetch_one_sql(connection, query, params=None):
    """Helper function to fetch one result using SQLAlchemy with a provided connection."""
    try:
        stmt = text(query)
        if params:
            for key, value in params.items():
                if isinstance(value, (list, tuple)):
                    stmt = stmt.bindparams(bindparam(key, expanding=True)) 
        result = connection.execute(stmt, params).fetchone()
        return result
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

def fetch_all_sql_df(connection, query, params=None):
    try:
        stmt = text(query)
        if params:
            for key, value in params.items():
                if isinstance(value, (list, tuple)):
                    stmt = stmt.bindparams(bindparam(key, expanding=True))
        result = connection.execute(stmt, params)
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=result.keys())
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

def fetch_all_sql_df(connection, query, params=None):
    """Fetch all results and return a pandas DataFrame."""
    try:
        stmt = text(query)
        if params:
            for key, value in params.items():
                if isinstance(value, (list, tuple)):
                    stmt = stmt.bindparams(bindparam(key, expanding=True))
        result = connection.execute(stmt, params)
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=result.keys())
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")