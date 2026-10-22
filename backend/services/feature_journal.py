
import json

from backend.database.feature_store import db_session


def create_entry(
    title,
    hypothesis="",
    body="",
    asset_ids=None,
    evidence=None,
    user_id="local",
):
    title = (title or "").strip()

    if not title:
        raise ValueError("Title is required")

    with db_session() as c:
        cur = c.execute(
            """
            INSERT INTO research_entries (
                user_id,
                title,
                hypothesis,
                body,
                asset_ids_json,
                evidence_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                title,
                hypothesis,
                body,
                json.dumps(asset_ids or []),
                json.dumps(evidence or {}),
            ),
        )
        return cur.lastrowid


def list_entries(user_id="local", limit=100):
    with db_session() as c:
        rows = c.execute(
            """
            SELECT *
            FROM research_entries
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_id, max(1, min(int(limit), 500))),
        ).fetchall()

    entries = []

    for row in rows:
        item = dict(row)
        item["asset_ids"] = json.loads(
            item.pop("asset_ids_json") or "[]"
        )
        item["evidence"] = json.loads(
            item.pop("evidence_json") or "{}"
        )
        item.pop("strategy_run_json", None)
        entries.append(item)

    return entries

def update_entry(
    entry_id,
    title,
    hypothesis="",
    body="",
    asset_ids=None,
    evidence=None,
    user_id="local",
):
    title = (title or "").strip()

    if not title:
        raise ValueError("Title is required")

    with db_session() as c:
        cur = c.execute(
            """
            UPDATE research_entries
            SET title = ?,
                hypothesis = ?,
                body = ?,
                asset_ids_json = ?,
                evidence_json = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (
                title,
                hypothesis,
                body,
                json.dumps(asset_ids or []),
                json.dumps(evidence or {}),
                entry_id,
                user_id,
            ),
        )

        return cur.rowcount > 0


def delete_entry(entry_id, user_id="local"):
    with db_session() as c:
        cur = c.execute(
            """
            DELETE FROM research_entries
            WHERE id = ? AND user_id = ?
            """,
            (entry_id, user_id),
        )

        return cur.rowcount > 0
