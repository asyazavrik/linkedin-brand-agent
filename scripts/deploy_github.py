#!/usr/bin/env python3
"""Deploy linkedin-brand-agent to GitHub via API."""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request

OWNER = "asyazavrik"
REPO = "linkedin-brand-agent"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"deploy_github.ps1", "deploy_github.py"}


def api(method: str, path: str, token: str, data: dict | None = None):
    url = f"https://api.github.com{path}"
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "linkedin-brand-agent",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def new_blob(token: str, path: str) -> str:
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode("ascii")
    result = api("POST", f"/repos/{OWNER}/{REPO}/git/blobs", token, {
        "content": content,
        "encoding": "base64",
    })
    return result["sha"]


def build_tree(token: str, directory: str) -> list[dict]:
    entries: list[dict] = []
    for name in sorted(os.listdir(directory)):
        full = os.path.join(directory, name)
        if os.path.isfile(full):
            if name in SKIP:
                continue
            entries.append({
                "path": name,
                "mode": "100644",
                "type": "blob",
                "sha": new_blob(token, full),
            })
        elif os.path.isdir(full):
            sub = build_tree(token, full)
            if sub:
                subtree = api("POST", f"/repos/{OWNER}/{REPO}/git/trees", token, {"tree": sub})
                entries.append({
                    "path": name,
                    "mode": "040000",
                    "type": "tree",
                    "sha": subtree["sha"],
                })
    return entries


def set_secrets(token: str, secrets: dict[str, str]) -> None:
    try:
        from nacl import encoding, public
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pynacl", "-q"])
        from nacl import encoding, public

    pub = api("GET", f"/repos/{OWNER}/{REPO}/actions/secrets/public-key", token)
    pk = public.PublicKey(pub["key"].encode(), encoding.Base64Encoder())
    box = public.SealedBox(pk)
    for name, value in secrets.items():
        encrypted = base64.b64encode(box.encrypt(value.encode())).decode()
        api("PUT", f"/repos/{OWNER}/{REPO}/actions/secrets/{name}", token, {
            "encrypted_value": encrypted,
            "key_id": pub["key_id"],
        })
        print(f"SECRET {name}")


def main() -> None:
    token = sys.argv[1]
    print("Building tree...")
    tree_entries = build_tree(token, ROOT)
    tree = api("POST", f"/repos/{OWNER}/{REPO}/git/trees", token, {"tree": tree_entries})
    commit = api("POST", f"/repos/{OWNER}/{REPO}/git/commits", token, {
        "message": "Initial deploy: LinkedIn brand agent for Nastya",
        "tree": tree["sha"],
    })
    try:
        api("POST", f"/repos/{OWNER}/{REPO}/git/refs", token, {
            "ref": "refs/heads/main",
            "sha": commit["sha"],
        })
    except urllib.error.HTTPError as exc:
        if exc.code != 422:
            raise
        api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/main", token, {
            "sha": commit["sha"],
            "force": True,
        })
    print(f"Pushed {commit['sha'][:7]}")

    parent = os.path.dirname(ROOT)
    deepseek_file = next(
        (os.path.join(parent, n) for n in os.listdir(parent) if n.startswith("sk-") and n.endswith(".txt")),
        None,
    )
    if not deepseek_file:
        raise SystemExit("DeepSeek key file not found")
    with open(deepseek_file, encoding="utf-8") as f:
        deepseek = f.read().strip()

    set_secrets(token, {
        "TELEGRAM_BOT_TOKEN": "8777535229:AAHs4ZgjJQ-3Oixrbpwf-eFu8PovoGKsgcQ",
        "TELEGRAM_CHAT_ID": "874111772",
        "DEEPSEEK_API_KEY": deepseek,
    })

    api("POST", f"/repos/{OWNER}/{REPO}/actions/workflows/morning_digest.yml/dispatches", token, {
        "ref": "main",
    })
    print("Workflow triggered")
    print(f"DONE https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
