import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sets.db")


def connect(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("""
        CREATE TABLE IF NOT EXISTS sets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user        TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            video_name  TEXT,
            score       REAL,
            max_score   REAL,
            main_tip    TEXT,
            checks_json TEXT
        )
    """)
    return db


def save_set(user, video_name, result, db_path=DB_PATH):
    with connect(db_path) as db:
        cursor = db.execute(
            "INSERT INTO sets (user, created_at, video_name, score, max_score, "
            "main_tip, checks_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user.strip().lower(),
                datetime.now().isoformat(timespec="seconds"),
                video_name,
                result.get("score"),
                result.get("max_score"),
                result.get("main_tip"),
                json.dumps(result.get("checks", [])),
            ),
        )
        return cursor.lastrowid


def load_sets(user, db_path=DB_PATH):
    with connect(db_path) as db:
        rows = db.execute(
            "SELECT * FROM sets WHERE user = ? ORDER BY created_at, id",
            (user.strip().lower(),),
        ).fetchall()
    sets = []
    for row in rows:
        s = dict(row)
        s["checks"] = json.loads(s.pop("checks_json") or "[]")
        sets.append(s)
    return sets


def delete_set(user, set_id, db_path=DB_PATH):
    with connect(db_path) as db:
        db.execute("DELETE FROM sets WHERE id = ? AND user = ?",
                   (set_id, user.strip().lower()))
