#!/usr/bin/env python3
"""Отправить утренний дайджест в Telegram."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.digest import build_digest
from src.telegram_client import TelegramClient

if __name__ == "__main__":
    text = build_digest()
    TelegramClient().send_message(text)
    print("Digest sent")
