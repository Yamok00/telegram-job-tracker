from fastapi import FastAPI, BackgroundTasks, Form, Depends, Request
from fastapi.responses import PlainTextResponse, Response
from typing import Annotated
from models import init_db, get_db
from sqlalchemy.orm import Session

from gmail_service import fetch_and_process_emails
from telegram_service import process_telegram_command, send_telegram_message
from config import settings
import requests

app = FastAPI(title="Ultimate Job Tracker API")

@app.on_event("startup")
def on_startup():
    init_db()
    print("Database initialized.")

def proactive_alert(body: str):
    if settings.user_telegram_chat_id:
        send_telegram_message(settings.user_telegram_chat_id, body)

@app.post("/sync")
def trigger_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Triggers a background historical sync of Gmail."""
    background_tasks.add_task(fetch_and_process_emails, db, proactive_alert)
    return {"status": "Sync started in background"}

@app.get("/set-webhook")
def set_webhook(url: str):
    """Register the webhook URL with Telegram."""
    if not settings.telegram_bot_token:
        return {"error": "Telegram Bot Token not configured."}
    
    webhook_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook?url={url}/webhook/telegram"
    r = requests.get(webhook_url)
    return r.json()

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives incoming updates from Telegram."""
    data = await request.json()
    
    if "message" in data:
        message = data["message"]
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        
        if text and chat_id:
            process_telegram_command(text, chat_id, db)
            
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
