# 🚀 Telegram Job Tracker Bot

An intelligent, cloud-hosted Telegram bot that autonomously monitors your Gmail to track job applications. It uses **Google Gemini 2.5 Flash** to classify emails into statuses like *Applied*, *Assessment*, *Interview*, *Offer*, or *Rejected* — and sends you real-time alerts via Telegram.

## ✨ Features

- **Automated Gmail Scanning** — Searches your inbox (including Spam & Trash) for job-related emails using keyword filtering.
- **AI-Powered Classification** — Uses Google Gemini to extract company name, role, status, and expertise level from raw email text.
- **Deduplication** — Tracks processed `message_id`s to avoid re-scanning the same email.
- **Proactive Telegram Alerts** — Sends you a notification when a new assessment or interview is detected.
- **Interactive Bot Commands** — Query your application data directly from Telegram:
  - `/start` — Welcome message with available commands.
  - `pending` — List applications waiting > 7 days for a response.
  - `summary` — Active application count grouped by status.
  - `list` — All applications grouped by status.
- **Cloud-Ready** — Designed for deployment on [Render](https://render.com) with a [Supabase](https://supabase.com) PostgreSQL database.

## 📁 Project Structure

| File | Description |
|---|---|
| `main.py` | FastAPI server — endpoints for `/sync`, `/set-webhook`, and the Telegram webhook. |
| `config.py` | Pydantic settings loaded from `.env`. |
| `models.py` | SQLAlchemy models (`Application`, `EmailReference`) with PostgreSQL/SQLite support. |
| `gmail_service.py` | Gmail OAuth2 authentication, email fetching, and processing pipeline. |
| `ai_service.py` | Gemini 2.5 Flash integration for email intent classification. |
| `telegram_service.py` | Telegram Bot API — sending messages and handling commands. |
| `requirements.txt` | Python dependencies. |

## 🛠️ Setup

### Prerequisites

- Python 3.10+
- A [Google Cloud](https://console.cloud.google.com/) project with the **Gmail API** enabled
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- A [Telegram Bot](https://core.telegram.org/bots#how-do-i-create-a-bot) (via @BotFather)
- A PostgreSQL database (e.g. [Supabase](https://supabase.com)) — *or SQLite for local dev*

### 1. Clone & Install

```bash
git clone https://github.com/Yamok00/telegram-job-tracker.git
cd telegram-job-tracker

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Fill in your `.env` with real credentials. See [`.env.example`](.env.example) for all required variables.

### 3. Gmail OAuth2 Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or use an existing one) and enable the **Gmail API**.
3. Navigate to **Credentials** → **Create Credentials** → **OAuth client ID**.
4. Choose **Desktop app**, download the JSON, and rename it to `credentials.json`.
5. Place `credentials.json` in the project root.
6. On first run, the app will open a browser window to authenticate and generate `token.json`.

> **Cloud Deployment Tip:** For headless environments (e.g. Render), set the `GOOGLE_TOKEN_JSON` environment variable with the full JSON contents of your `token.json` file instead.

### 4. Telegram Bot Setup

1. Message [@BotFather](https://t.me/BotFather) on Telegram and create a new bot.
2. Copy the **Bot Token** into `TELEGRAM_BOT_TOKEN` in your `.env`.
3. Send a message to your bot, then use the [Telegram API](https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates) to find your **Chat ID**. Set it as `USER_TELEGRAM_CHAT_ID`.
4. Register your webhook (after deploying):
   ```
   GET https://your-app-url.com/set-webhook?url=https://your-app-url.com
   ```

### 5. Run Locally

```bash
python main.py
```

The server starts on port `10000` by default (configurable via the `PORT` environment variable).

### 6. Trigger a Sync

```bash
curl -X POST http://localhost:10000/sync
```

This kicks off a background scan of your Gmail for job-related emails.

## ☁️ Deployment (Render)

1. Push your repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Set the **Build Command** to:
   ```
   pip install -r requirements.txt
   ```
4. Set the **Start Command** to:
   ```
   python main.py
   ```
5. Add all `.env` variables as **Environment Variables** in the Render dashboard.
6. Use a [Supabase](https://supabase.com) PostgreSQL database and set `DATABASE_URL` accordingly.
7. After deployment, register your Telegram webhook via the `/set-webhook` endpoint.

## 🔒 Security Notes

- **Never commit `.env`, `token.json`, or `credentials.json`** — they are listed in `.gitignore`.
- Use the `GOOGLE_TOKEN_JSON` env var for cloud deployments to avoid storing `token.json` on disk.
- Rotate any keys that have been accidentally exposed.

## 📄 License

MIT
