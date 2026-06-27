"""Утренний дайджест и ротация списка людей."""

from __future__ import annotations

import random
from datetime import datetime
from zoneinfo import ZoneInfo

from src.config import CONFIG_DIR, DATA_DIR, load_json, save_json
from src.comment_generator import generate_comment
from src.queue import mark_processed, pending_posts

MSK = ZoneInfo("Europe/Moscow")
STATE_PATH = DATA_DIR / "state.json"


def _load_targets() -> list[dict]:
    data = load_json(CONFIG_DIR / "targets.json", {"people": []})
    return data.get("people", [])


def _load_state() -> dict:
    return load_json(STATE_PATH, {"rotation_index": 0, "last_digest_date": ""})


def _save_state(state: dict) -> None:
    save_json(STATE_PATH, state)


def daily_target_count(now: datetime | None = None) -> int:
    now = now or datetime.now(MSK)
    if now.weekday() >= 5:
        return random.randint(0, 3)
    return random.randint(5, 15)


def rotation_slice(count: int = 5) -> tuple[list[dict], int]:
    people = _load_targets()
    if not people:
        return [], 0
    state = _load_state()
    start = state.get("rotation_index", 0) % len(people)
    picked = []
    for i in range(min(count, len(people))):
        picked.append(people[(start + i) % len(people)])
    next_index = (start + count) % len(people)
    return picked, next_index


def build_digest() -> str:
    now = datetime.now(MSK)
    target_n = daily_target_count(now)
    posts = pending_posts()

    if target_n == 0 and not posts:
        return (
            f"🌅 {now.strftime('%d.%m.%Y')} — выходной режим\n\n"
            "Сегодня можно отдохнуть от комментариев или добавить 1–2 ссылки вечером."
        )

    random.shuffle(posts)
    selected = posts[:target_n] if posts else []

    lines = [
        f"🌅 Дайджест LinkedIn — {now.strftime('%d.%m.%Y, %H:%M')} МСК",
        f"Сегодня в плане: {len(selected)} комментариев",
        "",
    ]

    if not selected:
        lines.extend(
            [
                "📭 В очереди пока нет ссылок на посты.",
                "",
                "Как добавить: отправь боту сообщение со ссылкой на пост LinkedIn.",
                "Например: https://www.linkedin.com/posts/...",
                "",
            ]
        )
    else:
        processed_ids: list[str] = []
        for idx, post in enumerate(selected, start=1):
            try:
                draft = generate_comment(post["url"], post.get("note", ""))
            except Exception as exc:  # noqa: BLE001 — digest should not fail entirely
                draft = f"⚠️ Не удалось сгенерировать: {exc}"

            lines.extend(
                [
                    f"{idx}️⃣ Пост",
                    f"🔗 {post['url']}",
                    "📝 Черновик:",
                    draft,
                    "",
                    "—" * 20,
                    "",
                ]
            )
            processed_ids.append(post["id"])

        mark_processed(processed_ids)

    rotate_n = 5
    people, next_idx = rotation_slice(rotate_n)
    if people:
        lines.append(f"👀 Сегодня глянь ленту у этих {len(people)} человек:")
        for person in people:
            name = person.get("name", "Без имени")
            company = person.get("company", "")
            url = person.get("linkedin_url", "")
            suffix = f" ({company})" if company else ""
            lines.append(f"• {name}{suffix}")
            if url:
                lines.append(f"  {url}")
        lines.append("")
        lines.append("Нашла интересный пост? Скинь ссылку боту — завтра будет черновик.")

        state = _load_state()
        state["rotation_index"] = next_idx
        state["last_digest_date"] = now.date().isoformat()
        _save_state(state)

    lines.append("")
    lines.append("✏️ Отредактируй черновик и опубликуй в LinkedIn вручную.")

    return "\n".join(lines)
