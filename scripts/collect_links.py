#!/usr/bin/env python3
"""Собрать новые ссылки из Telegram."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collect_links import collect_new_links, notify_collected

if __name__ == "__main__":
    count = collect_new_links()
    if count:
        notify_collected(count)
    print(f"Added {count} link(s)")
