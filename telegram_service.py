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

HELP_TEXT = (
    "📖 *Available Commands:*\n\n"
    "• *pending* — Jobs waiting > 7 days for a response\n"
    "• *summary* — Application count by status\n"
    "• *list* — All applications grouped by status\n\n"
    "_Filter by status:_\n"
    "• *rejected* — Rejected applications\n"
    "• *accepted* — Offers received\n"
    "• *applied* — Submitted / under review\n"
    "• *assessment* — Waiting for assessment\n"
    "• *interview* — Waiting for interview"
)

# Maps user-facing command → (DB status to match, emoji, display label)
STATUS_COMMANDS = {
    "rejected":   ("Rejected",   "❌", "Rejected Applications"),
    "accepted":   ("Offer",      "🎉", "Accepted / Offers"),
    "applied":    ("Applied",    "📬", "Applied / Under Review"),
    "assessment": ("Assessment", "📝", "Awaiting Assessment"),
    "interview":  ("Interview",  "🎤", "Awaiting Interview"),
}


def _filter_apps_by_status(db: Session, status: str, emoji: str, label: str) -> str:
    """Return a formatted reply listing all applications matching a given status."""
    apps = db.query(Application).filter(Application.status == status).all()
    
    if not apps:
        return f"{emoji} No *{label.lower()}* found."
    
    reply = f"{emoji} *{label}:* ({len(apps)})\n\n"
    for app in apps:
        days = app.days_since_update
        reply += f"• {app.company} — _{app.role}_ ({days}d ago)\n"
    
    if len(reply) > 4000:
        reply = reply[:4000] + "\n… (truncated)"
    
    return reply


def process_telegram_command(command_text: str, chat_id: str, db: Session):
    cmd = command_text.strip().lower()
    print(f"Received Command: '{cmd}' from {chat_id}")
    
    # --- Status filter commands ---
    if cmd in STATUS_COMMANDS:
        status, emoji, label = STATUS_COMMANDS[cmd]
        reply = _filter_apps_by_status(db, status, emoji, label)
        send_telegram_message(chat_id, reply)
        return
    
    if cmd == "pending":
        apps = db.query(Application).all()
        pending_apps = [app for app in apps if app.days_since_update > 7 and app.status not in ("Rejected", "Offer")]
        pending_apps.sort(key=lambda x: x.days_since_update, reverse=True)
        
        if not pending_apps:
            reply = "You have no pending applications waiting over 7 days for a response! 🎉"
        else:
            reply = "⏳ *Pending Responses:*\n\n"
            for app in pending_apps[:15]: 
                reply += f"• {app.company} — _{app.role}_: {app.days_since_update} days\n"
        
        send_telegram_message(chat_id, reply)
        
    elif cmd == "summary":
        apps = db.query(Application).all()
        
        stats = {}
        for app in apps:
            stats[app.status] = stats.get(app.status, 0) + 1
            
        reply = "📊 *Application Summary*\n\n"
        reply += f"Total Applications: {len(apps)}\n\n"
        for status, count in stats.items():
            reply += f"• {status}: {count}\n"
            
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
            reply += f"*{status.upper()}* ({len(app_list)})\n"
            for app in app_list:
                reply += f"• {app.company} — _{app.role}_\n"
            reply += "\n"
            
        if len(reply) > 4000:
            reply = reply[:4000] + "\n… (truncated)"
            
        send_telegram_message(chat_id, reply)
        
    elif cmd == "/start":
        reply = "🤖 *Welcome to the Ultimate Job Tracker Bot!*\n\n" + HELP_TEXT
        send_telegram_message(chat_id, reply)
        
    else:
        reply = "❓ Unknown command.\n\n" + HELP_TEXT
        send_telegram_message(chat_id, reply)
