import os.path
import base64
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import EmailReference, Application
from ai_service import analyze_email_intent
from config import settings

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    
    if settings.google_token_json:
        try:
            token_data = json.loads(settings.google_token_json)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"Error reading GOOGLE_TOKEN_JSON: {e}")
            
    if not creds and os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json') and not settings.google_token_json:
                print("Missing credentials.json and GOOGLE_TOKEN_JSON. Please configure authentication.")
                return None
            
            if os.path.exists('credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0, open_browser=False)
                
        # Only rewrite the local file if we aren't using the ENV var heavily
        if not settings.google_token_json:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def parse_parts(service, user_id, msg_id, payload):
    # Retrieve email body
    if payload.get('parts'):
        parts = payload.get('parts')
        data = ''
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                break
        if not data:
            return ""
    else:
        data = payload['body'].get('data')
        if not data:
            return ""
            
    try:
        clean_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return clean_text
    except Exception:
        return ""

def fetch_and_process_emails(db: Session, proactive_alert_callback=None):
    service = get_gmail_service()
    if not service:
        print("Could not initialize Gmail Service.")
        return
        
    # Get all existing message IDs for fast checking
    existing_ids = {ref.message_id for ref in db.query(EmailReference.message_id).all()}
    
    # Optional filtering to reduce the haystack, but pulling from all labels
    page_token = None
    processed_count = 0
    
    print("Starting historical sync deep scan...")
    
    while True:
        results = service.users().messages().list(
            userId='me', 
            includeSpamTrash=True, 
            q="{job application interview assessment engineer developer candidate offer applicant}",
            pageToken=page_token,
            maxResults=50
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("No more messages found in scan.")
            break
            
        for message in messages:
            msg_id = message['id']
            # Fast DB check for deduplication
            if msg_id in existing_ids:
                continue
                
            msg_detail = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            headers = msg_detail['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            
            body_text = parse_parts(service, 'me', msg_id, msg_detail['payload'])
            
            # Use Gemini to analyze the intent
            intent = analyze_email_intent(subject, sender, body_text)
            
            if intent.get("is_job_related") and intent.get("company_name"):
                company = intent.get("company_name")
                role = intent.get("role") or "Unknown Role"
                
                # Check if application exists
                app = db.query(Application).filter(Application.company == company, Application.role == role).first()
                if not app:
                    app = Application(
                        company=company,
                        role=role,
                        status=intent.get("status_summary") or "Applied",
                        expertise_level=intent.get("expertise_level") or "Generalist"
                    )
                    db.add(app)
                    db.commit()
                    db.refresh(app)
                else:
                    if intent.get("status_summary") != "Unknown" and intent.get("status_summary") != app.status:
                        app.status = intent.get("status_summary")
                        app.last_update_date = datetime.now()
                    db.commit()
                    db.refresh(app)
                
                # Add Email Reference
                email_ref = EmailReference(
                    message_id=msg_id,
                    thread_id=msg_detail.get('threadId', ''),
                    application_id=app.id,
                    subject=subject,
                    date_received=datetime.now() # Mock current date for parsing complexity
                )
                db.add(email_ref)
                db.commit()
                
                existing_ids.add(msg_id)
                
                # Proactive Telegram alerts for specific triggers
                if intent.get("is_new_assessment_or_invitation") and proactive_alert_callback:
                    alert_msg = f"🔔 *Action Required!* You have a new update from {company} for the {role} role.\nStatus: {app.status}\nSubject: {subject}"
                    proactive_alert_callback(alert_msg)
            else:
                # Add it so we don't scan it again
                email_ref = EmailReference(
                    message_id=msg_id,
                    thread_id=msg_detail.get('threadId', ''),
                    subject=subject,
                    date_received=datetime.now()
                )
                db.add(email_ref)
                db.commit()
                existing_ids.add(msg_id)
            
            processed_count += 1
            if processed_count >= 500: # Limit loop batches
                print("Processed 500 new emails. Stalling for next sync trigger.")
                return
                
        page_token = results.get('nextPageToken')
        if not page_token:
            break
            
    print(f"Finished deep scan. Processed {processed_count} emails.")
