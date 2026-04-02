import requests
from config import settings
from sqlalchemy.orm import Session
from models import Application
from datetime import datetime, timezone

def send_telegram_message(chat_id: str, text: str):
    if not settings.telegram_bot_token:
        print("Telegram bot token not set up. Skipping Telegram message.")
        print(f"Would have sent to {chat_id}: {text}")
        return
        
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Message sent to {chat_id}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def process_telegram_command(command_text: str, chat_id: str, db: Session):
    cmd = command_text.strip().lower()
    print(f"Received Command: '{cmd}' from {chat_id}")
    
    if cmd == "pending":
        apps = db.query(Application).all()
        # Find applications older than 7 days, excluding inactive statusses
        pending_apps = [app for app in apps if app.days_since_update > 7 and app.status not in ("Rejected", "Offer")]
        
        # Sort by days since update (descending)
        pending_apps.sort(key=lambda x: x.days_since_update, reverse=True)
        
        if not pending_apps:
            reply = "You have no pending applications waiting over 7 days for a response! 🎉"
        else:
            reply = "⏳ *Pending Responses:*\n\n"
            for app in pending_apps[:15]: 
                reply += f"- {app.company} ({app.role}): {app.days_since_update} days\n"
        
        send_telegram_message(chat_id, reply)
        
    elif cmd == "summary":
        apps = db.query(Application).all()
        active_apps = [a for a in apps if a.status not in ("Rejected", "Offer")]
        
        stats = {}
        for app in active_apps:
            stats[app.status] = stats.get(app.status, 0) + 1
            
        reply = "📊 *Application Summary*\n\n"
        reply += f"Active Applications: {len(active_apps)}\n"
        for status, count in stats.items():
            reply += f"- {status}: {count}\n"
            
        send_telegram_message(chat_id, reply)
        
    elif cmd == "list":
        apps = db.query(Application).all()
        if not apps:
            reply = "You haven't tracked any applications yet."
            send_telegram_message(chat_id, reply)
            return
            
        grouped = {}
        for app in apps:
            if app.status not in grouped:
                grouped[app.status] = []
            grouped[app.status].append(app)
            
        reply = "📋 *All Applications:*\n\n"
        for status, app_list in grouped.items():
            reply += f"*{status.upper()}*\n"
            for app in app_list:
                reply += f"- {app.company} ({app.role})\n"
            reply += "\n"
            
        # Telegram max length is 4096. Truncate if too long
        if len(reply) > 4000:
            reply = reply[:4000] + "\n... (Message truncated)"
            
        send_telegram_message(chat_id, reply)
        
    elif cmd == "/start":
        reply = "🤖 *Welcome to the Ultimate Job Tracker Bot!*\n\nAvailable commands:\n- *Pending*: List jobs waiting > 7 days.\n- *Summary*: Active applications count.\n- *List*: Show everything grouped by status."
        send_telegram_message(chat_id, reply)
        
    else:
        reply = "Unknown command.\n\nAvailable commands:\n- *Pending*: List jobs waiting > 7 days.\n- *Summary*: Active applications count.\n- *List*: Show everything grouped by status."
        send_telegram_message(chat_id, reply)
