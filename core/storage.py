"""Snapshots of issued papers.

The seed is not what gets stored. A later edit to a generator must not change
a paper that a school has already printed.
"""

import base64
import hashlib
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
            CREATE TABLE IF NOT EXISTS tutor_usage (
                membership_id TEXT PRIMARY KEY,
                uses INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(membership_id) REFERENCES memberships(membership_id)
            );
            CREATE TABLE IF NOT EXISTS muted_topics (
                membership_id TEXT NOT NULL,
                topic_key TEXT NOT NULL,
                muted_at TEXT,
                PRIMARY KEY (membership_id, topic_key)
            );
            CREATE TABLE IF NOT EXISTS saved_questions (
                question_id TEXT PRIMARY KEY,
                membership_id TEXT NOT NULL,
                topic_key TEXT,
                instance_key TEXT,
                created_at TEXT,
                payload_json TEXT
            );
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(muted_topics)")}
        for name, typedef in (
            ("topic_name", "TEXT"),
            ("section", "TEXT"),
            ("marks", "INTEGER"),
            ("level", "TEXT"),
            ("paper", "TEXT"),
        ):
            if name not in columns:
                connection.execute(f"ALTER TABLE muted_topics ADD COLUMN {name} {typedef}")


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


def get_tutor_uses(membership_id: str, path: Path | None = None) -> int:
    """How many successful tutor generations this membership has consumed."""
    if not membership_id:
        return 0
    init_db(path)
    with _connection(path) as connection:
        row = connection.execute(
            "SELECT uses FROM tutor_usage WHERE membership_id = ?",
            (membership_id,),
        ).fetchone()
    if row is None:
        return 0
    return int(row["uses"])


def increment_tutor_uses(membership_id: str, path: Path | None = None) -> int:
    """Record one successful tutor generation; returns the new total."""
    if not membership_id:
        raise ValueError("membership_id is required to record tutor usage.")
    init_db(path)
    with _connection(path) as connection:
        _touch_membership(connection, membership_id)
        row = connection.execute(
            "SELECT uses FROM tutor_usage WHERE membership_id = ?",
            (membership_id,),
        ).fetchone()
        uses = int(row["uses"]) if row else 0
        uses += 1
        connection.execute(
            """
            INSERT INTO tutor_usage (membership_id, uses) VALUES (?, ?)
            ON CONFLICT(membership_id) DO UPDATE SET uses = excluded.uses
            """,
            (membership_id, uses),
        )
    return uses


def tutor_uses_remaining(
    membership_id: str,
    limit: int,
    path: Path | None = None,
) -> int:
    return max(0, limit - get_tutor_uses(membership_id, path))


def question_instance_key(task: dict) -> str:
    """Identity of one generated question, ignoring the drawing and the cohort."""
    steps = []
    for group in task.get("markscheme") or []:
        if not isinstance(group, dict):
            continue
        for scheme_step in group.get("steps") or []:
            if isinstance(scheme_step, dict):
                steps.append(f"{scheme_step.get('code', '')}|{scheme_step.get('tex', '')}")
    table = task.get("table_data") or []
    raw = "\n".join(
        (
            str(task.get("latex_main") or ""),
            str(task.get("numeric_id") or ""),
            str(task.get("intro") or ""),
            " ".join(str(part) for part in task.get("subquestions") or []),
            "||".join(steps),
            json.dumps(table, ensure_ascii=False),
        )
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _encode_task(task: dict) -> dict:
    item = dict(task)
    item.pop("fig", None)
    raw = item.get("png_bytes")
    if isinstance(raw, bytes):
        item["png_bytes"] = {"__b64__": base64.b64encode(raw).decode("ascii")}
    return item


def _decode_task(task: dict) -> dict:
    item = dict(task)
    raw = item.get("png_bytes")
    if isinstance(raw, dict) and "__b64__" in raw:
        item["png_bytes"] = base64.b64decode(raw["__b64__"])
    return item


def mute_topic(
    membership_id: str,
    topic_key: str,
    path: Path | None = None,
    *,
    topic_name: str = "",
    section: str = "",
    marks: int | None = None,
    level: str = "",
    paper: str = "",
) -> None:
    if not membership_id:
        raise ValueError("membership_id is required to mute a topic.")
    if not topic_key:
        raise ValueError("topic_key is required to mute a topic.")
    init_db(path)
    with _connection(path) as connection:
        _touch_membership(connection, membership_id)
        connection.execute(
            """
            INSERT INTO muted_topics (
                membership_id, topic_key, muted_at, topic_name, section, marks, level, paper
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(membership_id, topic_key) DO UPDATE SET
                topic_name = CASE
                    WHEN excluded.topic_name != '' THEN excluded.topic_name
                    ELSE muted_topics.topic_name
                END,
                section = CASE
                    WHEN excluded.section != '' THEN excluded.section
                    ELSE muted_topics.section
                END,
                marks = COALESCE(excluded.marks, muted_topics.marks),
                level = CASE
                    WHEN excluded.level != '' THEN excluded.level
                    ELSE muted_topics.level
                END,
                paper = CASE
                    WHEN excluded.paper != '' THEN excluded.paper
                    ELSE muted_topics.paper
                END
            """,
            (
                membership_id,
                topic_key,
                _now(),
                topic_name or "",
                section or "",
                marks,
                level or "",
                paper or "",
            ),
        )


def block_topic(
    membership_id: str,
    topic_key: str,
    path: Path | None = None,
    **details,
) -> None:
    """Block one archetype. Saved question instances are left untouched."""
    mute_topic(membership_id, topic_key, path=path, **details)


def unblock_topic(membership_id: str, topic_key: str, path: Path | None = None) -> None:
    unmute_topic(membership_id, topic_key, path=path)


def unmute_topic(membership_id: str, topic_key: str, path: Path | None = None) -> None:
    if not membership_id:
        raise ValueError("membership_id is required to unmute a topic.")
    init_db(path)
    with _connection(path) as connection:
        connection.execute(
            "DELETE FROM muted_topics WHERE membership_id = ? AND topic_key = ?",
            (membership_id, topic_key),
        )


def unmute_all_topics(membership_id: str, path: Path | None = None) -> None:
    if not membership_id:
        raise ValueError("membership_id is required to restore muted topics.")
    init_db(path)
    with _connection(path) as connection:
        connection.execute(
            "DELETE FROM muted_topics WHERE membership_id = ?",
            (membership_id,),
        )


def list_muted_topics(membership_id: str, path: Path | None = None) -> list[str]:
    return [item["topic_key"] for item in list_blocked_topics(membership_id, path)]


def list_blocked_topics(membership_id: str, path: Path | None = None) -> list[dict]:
    if not membership_id:
        return []
    init_db(path)
    with _connection(path) as connection:
        rows = connection.execute(
            """
            SELECT topic_key, topic_name, section, marks, level, paper
            FROM muted_topics
            WHERE membership_id = ?
            ORDER BY topic_key
            """,
            (membership_id,),
        ).fetchall()
    return [
        {
            "topic_key": row["topic_key"],
            "archetype_key": row["topic_key"],
            "name": row["topic_name"] or "",
            "section": row["section"] or "",
            "marks": row["marks"],
            "level": row["level"] or "",
            "paper": row["paper"] or "",
        }
        for row in rows
    ]


def save_question_instance(
    membership_id: str,
    topic_key: str,
    task: dict,
    tutor_notes: str = "",
    path: Path | None = None,
    *,
    level: str = "",
    paper: str = "",
) -> str:
    """Store one generated question. Saving the same instance again keeps the first id."""
    if not membership_id:
        raise ValueError("membership_id is required to save a question.")
    if not isinstance(task, dict):
        raise TypeError("task must be the generated question dictionary.")
    init_db(path)
    instance_key = question_instance_key(task)
    payload = json.dumps(
        {
            "topic_key": topic_key,
            "archetype_key": topic_key,
            "level": level or "",
            "paper": paper or "",
            "tutor_notes": tutor_notes or "",
            "task": _encode_task(task),
        },
        ensure_ascii=False,
    )
    with _connection(path) as connection:
        _touch_membership(connection, membership_id)
        existing = connection.execute(
            """
            SELECT question_id FROM saved_questions
            WHERE membership_id = ? AND instance_key = ?
            """,
            (membership_id, instance_key),
        ).fetchone()
        if existing:
            return existing["question_id"]
        question_id = uuid.uuid4().hex
        connection.execute(
            """
            INSERT INTO saved_questions (
                question_id, membership_id, topic_key, instance_key, created_at, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (question_id, membership_id, topic_key, instance_key, _now(), payload),
        )
    return question_id


def clear_saved_questions(membership_id: str, path: Path | None = None) -> None:
    """Remove every saved question for this license. Blocked topics stay."""
    if not membership_id:
        raise ValueError("membership_id is required to clear saved questions.")
    init_db(path)
    with _connection(path) as connection:
        connection.execute(
            "DELETE FROM saved_questions WHERE membership_id = ?",
            (membership_id,),
        )


def clear_blocked_topics(membership_id: str, path: Path | None = None) -> None:
    """Unblock every archetype for this license. Saved questions stay."""
    unmute_all_topics(membership_id, path=path)


def delete_saved_question(membership_id: str, question_id: str, path: Path | None = None) -> None:
    if not membership_id:
        raise ValueError("membership_id is required to remove a saved question.")
    init_db(path)
    with _connection(path) as connection:
        connection.execute(
            "DELETE FROM saved_questions WHERE membership_id = ? AND question_id = ?",
            (membership_id, question_id),
        )


def list_saved_questions(membership_id: str, path: Path | None = None) -> list[dict]:
    if not membership_id:
        return []
    init_db(path)
    with _connection(path) as connection:
        rows = connection.execute(
            """
            SELECT question_id, topic_key, instance_key, created_at, payload_json
            FROM saved_questions
            WHERE membership_id = ?
            ORDER BY created_at
            """,
            (membership_id,),
        ).fetchall()
    found = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        task = _decode_task(payload.get("task") or {})
        found.append(
            {
                "question_id": row["question_id"],
                "topic_key": row["topic_key"] or payload.get("topic_key") or "",
                "archetype_key": payload.get("archetype_key") or row["topic_key"] or "",
                "level": payload.get("level") or "",
                "paper": payload.get("paper") or "",
                "instance_key": row["instance_key"],
                "created_at": row["created_at"],
                "tutor_notes": payload.get("tutor_notes") or "",
                "task": task,
            }
        )
    return found


def export_archive_json(membership_id: str, path: Path | None = None) -> str:
    """Issued papers and class lists for one license, as a JSON document."""
    init_db(path)
    with _connection(path) as connection:
        papers = connection.execute(
            """
            SELECT paper_id, title, created_at, paper_type, difficulty, total_marks, payload_json
            FROM saved_papers
            WHERE membership_id = ?
            ORDER BY created_at
            """,
            (membership_id,),
        ).fetchall()
        classes = connection.execute(
            """
            SELECT class_id, class_name, completed_topics
            FROM class_syllabi
            WHERE membership_id = ?
            ORDER BY class_name
            """,
            (membership_id,),
        ).fetchall()
    document = {
        "format": "stem-issued-v1",
        "papers": [
            {
                "paper_id": row["paper_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "paper_type": row["paper_type"],
                "difficulty": row["difficulty"],
                "total_marks": row["total_marks"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in papers
        ],
        "classes": [
            {
                "class_id": row["class_id"],
                "class_name": row["class_name"],
                "topics": json.loads(row["completed_topics"]),
            }
            for row in classes
        ],
        "muted_topics": list_muted_topics(membership_id, path),
        "blocked_topics": list_blocked_topics(membership_id, path),
        "saved_questions": [
            {
                "question_id": item["question_id"],
                "created_at": item["created_at"],
                "topic_key": item["topic_key"],
                "archetype_key": item.get("archetype_key") or item["topic_key"],
                "level": item.get("level") or "",
                "paper": item.get("paper") or "",
                "instance_key": item["instance_key"],
                "tutor_notes": item["tutor_notes"],
                "task": _encode_task(item["task"]),
            }
            for item in list_saved_questions(membership_id, path)
        ],
    }
    return json.dumps(document, ensure_ascii=False)


def import_archive_json(membership_id: str, raw: str, path: Path | None = None) -> int:
    """Restore an export onto this license. Returns how many papers were added."""
    if not membership_id:
        raise ValueError("membership_id is required to import an archive.")
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("The archive file is not JSON.") from exc
    if not isinstance(document, dict) or document.get("format") != "stem-issued-v1":
        raise ValueError("This file is not an Issued archive.")
    papers = document.get("papers") or []
    classes = document.get("classes") or []
    muted = document.get("muted_topics") or []
    blocked = document.get("blocked_topics") or []
    saved = document.get("saved_questions") or []
    if not isinstance(papers, list) or not isinstance(classes, list):
        raise ValueError("This file is not an Issued archive.")
    if not isinstance(muted, list) or not isinstance(blocked, list) or not isinstance(saved, list):
        raise ValueError("This file is not an Issued archive.")
    init_db(path)
    added = 0
    with _connection(path) as connection:
        _touch_membership(connection, membership_id)
        for item in papers:
            if not isinstance(item, dict) or not item.get("paper_id"):
                continue
            existing = connection.execute(
                "SELECT 1 FROM saved_papers WHERE paper_id = ?",
                (item["paper_id"],),
            ).fetchone()
            if existing:
                continue
            connection.execute(
                """
                INSERT INTO saved_papers (
                    paper_id, membership_id, title, created_at, paper_type,
                    difficulty, total_marks, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["paper_id"],
                    membership_id,
                    item.get("title") or "Untitled paper",
                    item.get("created_at") or _now(),
                    item.get("paper_type") or "",
                    item.get("difficulty") or "",
                    int(item.get("total_marks") or 0),
                    json.dumps(item.get("payload") or {}, ensure_ascii=False),
                ),
            )
            added += 1
        for item in classes:
            if not isinstance(item, dict) or not item.get("class_id"):
                continue
            existing = connection.execute(
                "SELECT 1 FROM class_syllabi WHERE class_id = ?",
                (item["class_id"],),
            ).fetchone()
            if existing:
                continue
            connection.execute(
                """
                INSERT INTO class_syllabi (class_id, membership_id, class_name, completed_topics)
                VALUES (?, ?, ?, ?)
                """,
                (
                    item["class_id"],
                    membership_id,
                    item.get("class_name") or "Class",
                    json.dumps(list(item.get("topics") or [])),
                ),
            )
        for topic_key in muted:
            if not isinstance(topic_key, str) or not topic_key:
                continue
            connection.execute(
                """
                INSERT INTO muted_topics (membership_id, topic_key, muted_at)
                VALUES (?, ?, ?)
                ON CONFLICT(membership_id, topic_key) DO NOTHING
                """,
                (membership_id, topic_key, _now()),
            )
        for item in blocked:
            if isinstance(item, str):
                topic_key = item
                details = {}
            elif isinstance(item, dict) and item.get("topic_key"):
                topic_key = item["topic_key"]
                details = item
            else:
                continue
            connection.execute(
                """
                INSERT INTO muted_topics (
                    membership_id, topic_key, muted_at, topic_name, section, marks, level, paper
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(membership_id, topic_key) DO UPDATE SET
                    topic_name = CASE
                        WHEN excluded.topic_name != '' THEN excluded.topic_name
                        ELSE muted_topics.topic_name
                    END,
                    section = CASE
                        WHEN excluded.section != '' THEN excluded.section
                        ELSE muted_topics.section
                    END,
                    marks = COALESCE(excluded.marks, muted_topics.marks),
                    level = CASE
                        WHEN excluded.level != '' THEN excluded.level
                        ELSE muted_topics.level
                    END,
                    paper = CASE
                        WHEN excluded.paper != '' THEN excluded.paper
                        ELSE muted_topics.paper
                    END
                """,
                (
                    membership_id,
                    topic_key,
                    _now(),
                    details.get("name") or details.get("topic_name") or "",
                    details.get("section") or "",
                    details.get("marks"),
                    details.get("level") or "",
                    details.get("paper") or "",
                ),
            )
        for item in saved:
            if not isinstance(item, dict) or not item.get("question_id"):
                continue
            task = item.get("task")
            if not isinstance(task, dict):
                continue
            instance_key = item.get("instance_key") or question_instance_key(_decode_task(task))
            existing = connection.execute(
                """
                SELECT 1 FROM saved_questions
                WHERE question_id = ? OR (membership_id = ? AND instance_key = ?)
                """,
                (item["question_id"], membership_id, instance_key),
            ).fetchone()
            if existing:
                continue
            connection.execute(
                """
                INSERT INTO saved_questions (
                    question_id, membership_id, topic_key, instance_key, created_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item["question_id"],
                    membership_id,
                    item.get("topic_key") or "",
                    instance_key,
                    item.get("created_at") or _now(),
                    json.dumps(
                        {
                            "topic_key": item.get("topic_key") or item.get("archetype_key") or "",
                            "archetype_key": item.get("archetype_key") or item.get("topic_key") or "",
                            "level": item.get("level") or "",
                            "paper": item.get("paper") or "",
                            "tutor_notes": item.get("tutor_notes") or "",
                            "task": task,
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
    return added
