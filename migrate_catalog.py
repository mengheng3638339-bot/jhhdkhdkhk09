import os
import sqlite3
from contextlib import closing
from pathlib import Path

from database import connect
from bot import initialize_catalog


SQLITE_PATH = Path(__file__).resolve().with_name("file_catalog.sqlite3")


def main() -> None:
    if not os.environ.get("DATABASE_URL", "").strip():
        raise RuntimeError("Set DATABASE_URL to the PostgreSQL connection string first.")
    if not SQLITE_PATH.is_file():
        raise FileNotFoundError(f"Local catalog database not found: {SQLITE_PATH}")

    initialize_catalog()

    with closing(sqlite3.connect(SQLITE_PATH)) as source:
        files = source.execute(
            """
            SELECT file_name, file_id, media_type, callback_key, uploaded_by, status, uploaded_at
            FROM files
            """
        ).fetchall()
        users = source.execute(
            "SELECT user_id, username, first_name, last_name, last_seen FROM known_users"
        ).fetchall()
        banned_users = source.execute(
            "SELECT user_id, banned_at FROM banned_users"
        ).fetchall()

    with closing(connect(str(SQLITE_PATH))) as destination:
        for file_row in files:
            destination.execute(
                """
                INSERT INTO files
                    (file_name, file_id, media_type, callback_key, uploaded_by, status, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                file_row,
            )
        for user_row in users:
            destination.execute(
                """
                INSERT INTO known_users
                    (user_id, username, first_name, last_name, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                user_row,
            )
        for banned_row in banned_users:
            destination.execute(
                """
                INSERT INTO banned_users (user_id, banned_at)
                VALUES (?, ?)
                ON CONFLICT DO NOTHING
                """,
                banned_row,
            )
        destination.commit()

    print(
        f"Copied {len(files)} catalog entries, {len(users)} users, "
        f"and {len(banned_users)} bans to PostgreSQL."
    )


if __name__ == "__main__":
    main()
