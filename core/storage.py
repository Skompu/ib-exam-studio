"""Snapshots of issued papers.

The seed is not what gets stored. A later edit to a generator must not change
a paper that a school has already printed.
"""

import base64
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = _ROOT / "storage" / "studio_data.db"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@contextmanager
def _connection(path: Path | None = None):
    database = Path(path) if path is not None else DEFAULT_DB
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(path: Path | None = None) -> None:
    with _connection(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS memberships (
                membership_id TEXT PRIMARY KEY,
                email TEXT,
                status TEXT,
                last_seen TEXT
            );
            CREATE TABLE IF NOT EXISTS saved_papers (
                paper_id TEXT PRIMARY KEY,
                membership_id TEXT,
                title TEXT,
                created_at TEXT,
                paper_type TEXT,
                difficulty TEXT,
                total_marks INTEGER,
                payload_json TEXT,
                FOREIGN KEY(membership_id) REFERENCES memberships(membership_id)
            );
            CREATE TABLE IF NOT EXISTS class_syllabi (
                class_id TEXT PRIMARY KEY,
                membership_id TEXT,
                class_name TEXT,
                completed_topics TEXT,
                FOREIGN KEY(membership_id) REFERENCES memberships(membership_id)
            );
            """
        )


def _touch_membership(connection, membership_id: str, status: str = "active") -> None:
    connection.execute(
        """
        INSERT INTO memberships (membership_id, email, status, last_seen)
        VALUES (?, '', ?, ?)
        ON CONFLICT(membership_id) DO UPDATE SET
            status = excluded.status,
            last_seen = excluded.last_seen
        """,
        (membership_id, status, _now()),
    )


def _encode_papers(papers: list) -> list:
    encoded = []
    for paper in papers:
        tasks = []
        for task in paper["tasks"]:
            item = dict(task)
            raw = item.get("png_bytes")
            if isinstance(raw, bytes):
                item["png_bytes"] = {"__b64__": base64.b64encode(raw).decode("ascii")}
            tasks.append(item)
        clone = dict(paper)
        clone["tasks"] = tasks
        encoded.append(clone)
    return encoded


def _decode_papers(papers: list) -> list:
    decoded = []
    for paper in papers:
        tasks = []
        for task in paper["tasks"]:
            item = dict(task)
            raw = item.get("png_bytes")
            if isinstance(raw, dict) and "__b64__" in raw:
                item["png_bytes"] = base64.b64decode(raw["__b64__"])
            tasks.append(item)
        clone = dict(paper)
        clone["tasks"] = tasks
        decoded.append(clone)
    return decoded


def save_paper_snapshot(
    membership_id: str,
    title: str,
    paper_type: str,
    difficulty: str,
    total_marks: int,
    papers_data: list,
    meta_dict: dict,
    path: Path | None = None,
) -> str:
    init_db(path)
    paper_id = uuid.uuid4().hex
    payload = json.dumps(
        {"papers": _encode_papers(papers_data), "meta": meta_dict},
        ensure_ascii=False,
    )
    with _connection(path) as connection:
        _touch_membership(connection, membership_id)
        connection.execute(
            """
            INSERT INTO saved_papers (
                paper_id, membership_id, title, created_at, paper_type,
                difficulty, total_marks, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (paper_id, membership_id, title.strip() or "Untitled paper", _now(), paper_type, difficulty, int(total_marks), payload),
        )
    return paper_id


def list_saved_papers(membership_id: str, path: Path | None = None) -> list[dict]:
    init_db(path)
    with _connection(path) as connection:
        rows = connection.execute(
            """
            SELECT paper_id, title, created_at, paper_type, difficulty, total_marks
            FROM saved_papers
            WHERE membership_id = ?
            ORDER BY created_at DESC
            """,
            (membership_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_paper_snapshot(paper_id: str, path: Path | None = None) -> dict:
    init_db(path)
    with _connection(path) as connection:
        row = connection.execute(
            """
            SELECT paper_id, membership_id, title, created_at, paper_type,
                   difficulty, total_marks, payload_json
            FROM saved_papers
            WHERE paper_id = ?
            """,
            (paper_id,),
        ).fetchone()
    if row is None:
        raise KeyError(f"No archived paper with id {paper_id}.")
    payload = json.loads(row["payload_json"])
    return {
        "paper_id": row["paper_id"],
        "membership_id": row["membership_id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "paper_type": row["paper_type"],
        "difficulty": row["difficulty"],
        "total_marks": row["total_marks"],
        "papers": _decode_papers(payload["papers"]),
        "meta": payload["meta"],
    }


def save_class_topics(
    membership_id: str,
    class_name: str,
    topics: list[str],
    path: Path | None = None,
) -> str:
    init_db(path)
    class_id = uuid.uuid4().hex
    with _connection(path) as connection:
        _touch_membership(connection, membership_id)
        connection.execute(
            """
            INSERT INTO class_syllabi (class_id, membership_id, class_name, completed_topics)
            VALUES (?, ?, ?, ?)
            """,
            (class_id, membership_id, class_name.strip() or "Class", json.dumps(list(topics))),
        )
    return class_id


def list_classes(membership_id: str, path: Path | None = None) -> list[dict]:
    init_db(path)
    with _connection(path) as connection:
        rows = connection.execute(
            """
            SELECT class_id, class_name, completed_topics
            FROM class_syllabi
            WHERE membership_id = ?
            ORDER BY class_name
            """,
            (membership_id,),
        ).fetchall()
    found = []
    for row in rows:
        found.append(
            {
                "class_id": row["class_id"],
                "class_name": row["class_name"],
                "topics": json.loads(row["completed_topics"]),
            }
        )
    return found
