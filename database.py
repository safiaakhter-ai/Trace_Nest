"""Local SQLite alert storage for TraceNest (no network/database server)."""
from __future__ import annotations

import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime
from pathlib import Path


def _data_directory() -> Path:
    # Under PyInstaller, __file__ points inside a temporary extraction
    # directory; never store the persistent database there.
    if getattr(sys, "frozen", False):
        app_data = os.environ.get("LOCALAPPDATA")
        base = Path(app_data) if app_data else Path.home() / "AppData" / "Local"
        folder = base / "TraceNest"
    else:
        folder = Path(__file__).resolve().parent
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def database_path() -> Path:
    return _data_directory() / "tracenest.db"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(str(database_path()), timeout=10)


def initialize_database() -> None:
    # Use an owned table name to avoid altering a user's existing schema.
    with closing(_connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tracenest_alert_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tracenest_alert_time
            ON tracenest_alert_log(timestamp)
        """)


def log_event(category: str, severity: str, message: str) -> None:
    initialize_database()
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO tracenest_alert_log(timestamp, category, severity, message) "
            "VALUES (?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             str(category), str(severity), str(message)),
        )


def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _legacy_rows(conn: sqlite3.Connection, limit: int):
    # Read old alert history without modifying old tables. Old versions may
    # have used alerts, alert_history, events, or logs as their table name.
    for table in ("alerts", "alert_history", "events", "logs"):
        found = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if not found:
            continue
        columns = [r[1] for r in conn.execute(
            f"PRAGMA table_info({_quoted(table)})"
        ).fetchall()]
        normalized = {c.lower(): c for c in columns}
        def choose(*options):
            return next((normalized[c] for c in options if c in normalized), None)
        dt = choose("timestamp", "created_at", "time", "event_time", "date")
        sev = choose("severity", "level")
        msg = choose("message", "description", "alert_message")
        if not (dt and sev and msg):
            continue
        sql = (
            f"SELECT {_quoted(dt)}, {_quoted(sev)}, {_quoted(msg)} "
            f"FROM {_quoted(table)} "
            f"ORDER BY {_quoted(dt)} DESC LIMIT ?"
        )
        try:
            yield from conn.execute(sql, (limit,)).fetchall()
        except sqlite3.DatabaseError:
            continue


def get_alert_history(limit: int = 500):
    initialize_database()
    rows = []
    with closing(_connect()) as conn:
        rows.extend(conn.execute(
            "SELECT timestamp, severity, message "
            "FROM tracenest_alert_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall())
        rows.extend(_legacy_rows(conn, limit))
    # Most historical timestamps use YYYY-MM-DD HH:MM:SS, so string
    # ordering yields newest-first. Avoid duplicate rows across tables.
    unique = {}
    for ts, severity, message in rows:
        row = (str(ts), str(severity), str(message))
        unique[row] = row
    return sorted(unique.values(), key=lambda row: row[0], reverse=True)[:limit]
