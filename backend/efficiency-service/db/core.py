import pandas as pd
from sqlalchemy import text, bindparam
from exceptions.exceptions import DatabaseException

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

def execute_sql_batch(connection, query, param_list):
    """
    Executes a batch SQL statement using a list of parameter dicts.
    """
    if not isinstance(param_list, list):
        raise DatabaseException("execute_sql_batch expects a list of parameter dictionaries.")

    try:
        stmt = text(query)
        if param_list:
            for key, value in param_list[0].items():
                if isinstance(value, (list, tuple)):
                    stmt = stmt.bindparams(bindparam(key, expanding=True))
        return connection.execute(stmt, param_list)
    except Exception as e:
        raise DatabaseException(f"Batch database error: {e}")


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
