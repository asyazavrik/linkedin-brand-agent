# LinkedIn Brand Agent для Насти

Утренний дайджест в Telegram: ссылки на посты + черновики комментариев в твоём стиле (TA в фарме).

Работает **бесплатно** на GitHub Actions + Telegram + **Groq** (для России вместо Gemini).

> 🇷🇺 Google AI Studio в РФ недоступен — см. [регионы Gemini](https://ai.google.dev/gemini-api/docs/available-regions?hl=ru). Используй Groq.

---

## Как это работает

1. **Вечером** ты кидаешь боту ссылки на посты LinkedIn.
2. **Каждый час** агент забирает ссылки и кладёт в очередь.
3. **В 7:30 МСК** приходит дайджест с черновиками (5–15 в будни, меньше в выходные).
4. **Ты правишь** и публикуешь комментарии вручную в LinkedIn.

---

## Шаг 1 — Создай Telegram-бота (5 минут)

1. Открой Telegram на телефоне или ноутбуке.
2. Найди **@BotFather** → нажми **Start**.
3. Отправь команду: `/newbot`
4. Имя бота (как видят люди): `Nastya LinkedIn Assistant`
5. Username (латиница, на `_bot`): например `nastya_linkedin_ta_bot`
6. BotFather пришлёт **токен** вида `7123456789:AAH...` — **сохрани его**.

### Узнай свой Chat ID

1. Найди **@userinfobot** в Telegram → Start.
2. Он пришлёт твой **Id** — это число, например `123456789`.

### Напиши боту первым

1. Найди своего нового бота по username.
2. Нажми **Start** — иначе он не сможет писать тебе.

---

## Шаг 2 — Ключ Groq (бесплатно, для России)

1. Включи VPN (Hiddify) → сервер **Казахстан** или **Турция**
2. [console.groq.com](https://console.groq.com) → регистрация
3. **API Keys** → **Create API Key** → скопируй `gsk_...`

Альтернатива: Gemini через VPN и [Google AI Studio](https://aistudio.google.com/apikey) — секрет `GEMINI_API_KEY`, в Actions добавь `AI_PROVIDER=gemini`.

---

## Шаг 3 — Залей проект на GitHub

### 3.1 Создай репозиторий

1. Зайди на [github.com/Asyazavrik](https://github.com/Asyazavrik)
2. **New repository** → имя: `linkedin-brand-agent` → **Create**.

### 3.2 Загрузи файлы

Самый простой способ без git в терминале:

1. В репозитории нажми **Add file** → **Upload files**
2. Перетащи **всю папку** `linkedin-brand-agent` с рабочего стола  
   (`Мои проекты\linkedin-brand-agent`)
3. **Commit changes**

### 3.3 Добавь секреты

В репозитории: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Имя | Значение |
|-----|----------|
| `TELEGRAM_BOT_TOKEN` | токен от BotFather |
| `TELEGRAM_CHAT_ID` | `874111772` |
| `GROQ_API_KEY` | ключ от Groq (`gsk_...`) |

---

## Шаг 4 — Список людей

Открой на GitHub файл `config/targets.json` → **Edit** → добавь своих 30 человек:

```json
{
  "name": "Имя Фамилия",
  "company": "Компания",
  "linkedin_url": "https://www.linkedin.com/in/...",
  "notes": ""
}
```

---

## Как пользоваться каждый день

### Вечером (5 минут)

Открой чат с ботом и отправь ссылки на посты:

```
https://www.linkedin.com/posts/ivanov-activity-123...
https://www.linkedin.com/posts/petrova-activity-456...
```

Можно с коротким комментарием — бот поймёт контекст.

### Утром (7:30)

Придёт сообщение с черновиками. Правишь → публикуешь в LinkedIn.

### Проверить вручную

На GitHub: вкладка **Actions** → **Morning digest** → **Run workflow**

---

## Как добавить ссылки сразу (тест)

После настройки секретов: **Actions** → **Collect LinkedIn links** → **Run workflow**

---

## Ноутбук: что уже сделано

- Отключён автозапуск Edge при входе в Windows.
- Диск и память в порядке (32 ГБ RAM, много свободного места).

### Если VK / LinkedIn тормозят

1. **Hiddify** — попробуй разные серверы или выключи на 5 минут и сравни скорость.
2. **LinkedIn** — часто быстрее через VPN с сервером в EU/TR/KZ.
3. **VK** — часто быстрее **без** VPN (российский трафик).
4. Закрой лишние вкладки Chrome (у тебя было ~18 процессов).
5. DNS (по желанию): Параметры → Сеть → Wi‑Fi → DNS → `1.1.1.1` и `8.8.8.8`.

### Режим питания

Сейчас «Сбалансированный». Если нужна скорость — можно включить **Razer Cortex Power Plan** (больше расход батареи).

---

## Вопросы

Пиши в чат с Cursor — разберём вместе.
