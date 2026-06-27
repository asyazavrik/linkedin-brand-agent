"""Генерация черновиков комментариев (DeepSeek — работает из России)."""

from __future__ import annotations

import os

import requests

from src.config import CONFIG_DIR, require_env

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _load_style() -> str:
    return (CONFIG_DIR / "style_prompt.txt").read_text(encoding="utf-8")


def _build_prompt(post_url: str, post_text: str, author: str) -> str:
    user_parts = [f"Ссылка на пост: {post_url}"]
    if author:
        user_parts.append(f"Автор: {author}")
    if post_text.strip():
        user_parts.append(f"Текст поста (если известен):\n{post_text.strip()}")
    else:
        user_parts.append(
            "Текст поста неизвестен — напиши универсальный, но осмысленный "
            "черновик комментария для TA-эксперта в фарме, который можно "
            "слегка подправить после прочтения поста."
        )
    return f"{_load_style()}\n\n---\n\n" + "\n".join(user_parts)


def _chat_completion(url: str, api_key: str, model: str, prompt: str) -> str:
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.75,
            "max_tokens": 500,
        },
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    return (data["choices"][0]["message"]["content"] or "").strip()


def _generate_with_deepseek(prompt: str) -> str:
    return _chat_completion(
        DEEPSEEK_URL, require_env("DEEPSEEK_API_KEY"), DEEPSEEK_MODEL, prompt
    )


def _generate_with_groq(prompt: str) -> str:
    return _chat_completion(
        GROQ_URL, require_env("GROQ_API_KEY"), GROQ_MODEL, prompt
    )


def _generate_with_gemini(prompt: str) -> str:
    import google.generativeai as genai

    api_key = require_env("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return (response.text or "").strip()


def generate_comment(post_url: str, post_text: str = "", author: str = "") -> str:
    prompt = _build_prompt(post_url, post_text, author)
    provider = os.environ.get("AI_PROVIDER", "deepseek").strip().lower()

    providers = {
        "deepseek": ("DEEPSEEK_API_KEY", _generate_with_deepseek),
        "groq": ("GROQ_API_KEY", _generate_with_groq),
        "gemini": ("GEMINI_API_KEY", _generate_with_gemini),
    }

    if provider in providers:
        env_name, func = providers[provider]
        if os.environ.get(env_name):
            return func(prompt)

    for env_name, func in [
        ("DEEPSEEK_API_KEY", _generate_with_deepseek),
        ("GROQ_API_KEY", _generate_with_groq),
        ("GEMINI_API_KEY", _generate_with_gemini),
    ]:
        if os.environ.get(env_name):
            return func(prompt)

    raise RuntimeError(
        "Нужен DEEPSEEK_API_KEY в секретах GitHub (рекомендуется для России)"
    )
