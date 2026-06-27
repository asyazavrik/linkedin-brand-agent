"""Клиент Telegram Bot API."""

from __future__ import annotations

import re
from typing import Any

import requests

from src.config import require_env

API_BASE = "https://api.telegram.org/bot{token}/{method}"
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/\S+", re.I)


class TelegramClient:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = token or require_env("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or require_env("TELEGRAM_CHAT_ID")

    def _call(self, method: str, **payload: Any) -> dict:
        url = API_BASE.format(token=self.token, method=method)
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
        return data

    def send_message(self, text: str, disable_preview: bool = False) -> None:
        # Telegram limit 4096 chars — split if needed
        chunks = [text[i : i + 4000] for i in range(0, len(text), 4000)] or [text]
        for chunk in chunks:
            self._call(
                "sendMessage",
                chat_id=self.chat_id,
                text=chunk,
                disable_web_page_preview=disable_preview,
            )

    def get_updates(self, offset: int | None = None, timeout: int = 0) -> list[dict]:
        payload: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset
        data = self._call("getUpdates", **payload)
        return data.get("result", [])

    @staticmethod
    def extract_linkedin_urls(text: str) -> list[str]:
        return LINKEDIN_RE.findall(text or "")
