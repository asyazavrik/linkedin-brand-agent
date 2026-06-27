"""Очередь постов для обработки."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.config import DATA_DIR, load_json, save_json

QUEUE_PATH = DATA_DIR / "queue.json"
STATE_PATH = DATA_DIR / "state.json"
OFFSET_PATH = DATA_DIR / "offset.txt"


def load_queue() -> dict:
    return load_json(QUEUE_PATH, {"posts": []})


def save_queue(queue: dict) -> None:
    save_json(QUEUE_PATH, queue)


def add_post(url: str, note: str = "") -> bool:
    queue = load_queue()
    urls = {p["url"] for p in queue.get("posts", [])}
    if url in urls:
        return False
    queue.setdefault("posts", []).append(
        {
            "id": str(uuid4())[:8],
            "url": url,
            "note": note.strip(),
            "added_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }
    )
    save_queue(queue)
    return True


def pending_posts() -> list[dict]:
    return [p for p in load_queue().get("posts", []) if p.get("status") == "pending"]


def mark_processed(post_ids: list[str]) -> None:
    queue = load_queue()
    for post in queue.get("posts", []):
        if post.get("id") in post_ids:
            post["status"] = "processed"
    save_queue(queue)


def load_offset() -> int | None:
    if not OFFSET_PATH.exists():
        return None
    raw = OFFSET_PATH.read_text(encoding="utf-8").strip()
    return int(raw) if raw else None


def save_offset(offset: int) -> None:
    OFFSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    OFFSET_PATH.write_text(str(offset), encoding="utf-8")
