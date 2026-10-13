import os
import re
import sqlite3
from typing import Any


def postgres_query(query: str) -> str:
    ignore_conflicts = "INSERT OR IGNORE" in query
    query = re.sub(
        r"ORDER BY ([\w.]+) COLLATE NOCASE",
        r"ORDER BY lower(\1)",
        query,
        flags=re.IGNORECASE,
    )
    query = query.replace("ON CONFLICT(file_name)", "ON CONFLICT (lower(file_name))")
    if ignore_conflicts:
        query = query.replace("INSERT OR IGNORE INTO", "INSERT INTO")
        query = f"{query.rstrip().rstrip(';')} ON CONFLICT DO NOTHING"
    return query.replace("?", "%s")


def using_postgres() -> bool:
    return bool(os.environ.get("DATABASE_URL", "").strip())


def connect(database_path: str) -> Any:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        return sqlite3.connect(database_path)

    import psycopg
    from psycopg import errors

    class PostgresConnection:
        def __init__(self, connection: Any) -> None:
            self._connection = connection

        def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> Any:
            query = postgres_query(query)
            try:
                return self._connection.execute(query, parameters)
            except errors.IntegrityError as error:
                raise sqlite3.IntegrityError(str(error)) from error
            except psycopg.Error as error:
                raise sqlite3.Error(str(error)) from error

        def commit(self) -> None:
            try:
                self._connection.commit()
            except errors.IntegrityError as error:
                raise sqlite3.IntegrityError(str(error)) from error
            except psycopg.Error as error:
                raise sqlite3.Error(str(error)) from error

        def close(self) -> None:
            self._connection.close()

    try:
        connection = psycopg.connect(database_url, connect_timeout=10)
    except psycopg.Error as error:
        raise sqlite3.Error(str(error)) from error
    return PostgresConnection(connection)
