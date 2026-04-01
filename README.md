# Ultimate Job Tracker & WhatsApp Career Assistant

This system autonomously monitors your Gmail history (including Spam and Trash) to track your job applications and statuses. It uses Google Gemini Pro to classify messages into statuses such as "Applied", "Assessment", or "Interview". It flags "Pending Response" records and integrates with WhatsApp via Twilio to send reactive commands and proactive alerts.

## Project Structure
- `config.py`: Environment configurations based on `.env`.
- `models.py`: Database schema layout with Deduplication logic to prevent parsing the same `message_id`.
- `gmail_service.py`: Authentication to Gmail, search filtering logic, and text extraction logic.
- `ai_service.py`: Calling Gemini Pro to parse and format the unstructured text into a predetermined JSON format.
- `whatsapp_service.py`: Twilio interface logic parsing text strings like `"Pending"` or `"Summary"`.
- `main.py`: The FastAPI application server hosting Background Tasks and Webhooks.

## Setup Instructions

### 1. Zero-Error Environment Setup
Ensure you are using Python 3.10+
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Fill out `.env` with your secure keys.

### 2. Gmail OAuth2 Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and enable the **Gmail API**.
3. Go to "Credentials", click "Create Credentials", and choose "OAuth client ID".
4. Choose "Desktop app" (or your appropriate type).
5. Download the JSON file, and rename it to `credentials.json`.
6. Place `credentials.json` directly in this folder.
7. Upon the first execution of the deep scan, it will open a browser to authenticate and create `token.json`.

### 3. Twilio WhatsApp Setup
1. Create a free Twilio account and activate the [Twilio Sandbox for WhatsApp](https://www.twilio.com/console/sms/whatsapp/learn).
2. Connect your personal number to the Sandbox.
3. In Twilio, set the Sandbox configuration webhook to your FastAPI backend port endpoint (e.g. `https://your-ngrok-url/webhook/whatsapp`). *Note: because this handles incoming traffic, you must use something like NGROK to expose port 8000.*

### 4. Running the App
Start the Uvicorn server:
```bash
uvicorn main:app --reload
```

Then trigger the background sync:
```bash
curl -X POST http://localhost:8000/sync
```

Watch the terminal as it iteratively checks historical chunks of your email messages, runs inference, and writes application states to SQLite!
