"""Сбор ссылок из входящих сообщений Telegram."""

from __future__ import annotations

from src.queue import add_post, load_offset, save_offset
from src.telegram_client import TelegramClient


def collect_new_links() -> int:
    client = TelegramClient()
    offset = load_offset()
    updates = client.get_updates(offset=offset)
    added = 0
    max_update_id = offset

    for update in updates:
        update_id = update.get("update_id", 0)
        max_update_id = max(max_update_id or 0, update_id)
        message = update.get("message") or update.get("edited_message")
        if not message:
            continue
        text = message.get("text") or message.get("caption") or ""
        if text.strip().startswith("/start"):
            client.send_message(
                "Привет, Настя! 👋\n\n"
                "Кидай сюда ссылки на посты LinkedIn — утром в 7:30 пришлю черновики комментариев.\n\n"
                "Пример:\nhttps://www.linkedin.com/posts/..."
            )
            continue
        for url in TelegramClient.extract_linkedin_urls(text):
            if add_post(url, note=text):
                added += 1

    if max_update_id is not None and updates:
        save_offset(max_update_id + 1)

    return added


def notify_collected(added: int) -> None:
    client = TelegramClient()
    if added:
        client.send_message(
            f"✅ Добавила {added} ссылок в очередь. Утром пришлю черновики!"
        )
