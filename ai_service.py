import google.generativeai as genai
from config import settings
import json

genai.configure(api_key=settings.gemini_api_key)

SYSTEM_PROMPT = """You are a highly intelligent Career Assistant AI for a Software Engineer. The user has specialized knowledge in complex medical and technical terminology like Pathology, RAG (Retrieval-Augmented Generation), and FastAPI.
Your task is to analyze the content of raw incoming emails and extract structured information about job applications.

Instructions:
1. Determine if the email is related to a job application.
2. Extract the 'company_name' and 'role'.
3. Categorize 'expertise_level' as 'Expert' if the role or email text involves advanced topics like RAG, AI integration, advanced FastAPI architectures, or medical terminology (e.g., Pathology). Otherwise, it is 'Generalist'.
4. Determine 'is_automation_receipt'. Set to true if the email is an automated "we received your application" or similar auto-responder mail. Set to false if it implies human review or next steps.
5. Determine 'is_new_assessment_or_invitation'. Set to true if the email is asking the user to take an assessment (like HackerRank, specific take-home) or setting up an interview.
6. Determine 'status_summary' which should be one of: "Applied", "Assessment", "Interview", "Offer", "Rejected", "Update". 

Respond exactly with the following JSON schema:
{
  "is_job_related": boolean,
  "company_name": string | null,
  "role": string | null,
  "is_automation_receipt": boolean,
  "is_new_assessment_or_invitation": boolean,
  "status_summary": string,
  "expertise_level": string
}
"""

def analyze_email_intent(subject: str, sender: str, body: str) -> dict:
    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
        # Fallback if unconfigured for safety
        return _fallback_response()
        
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f'''
        Analyze the following email.
        
        Subject: {subject}
        Sender: {sender}
        Body: 
        {body[:3000]} # Limit body size to prevent context overflow for huge emails
        '''
        
        response = model.generate_content(
            [{"role": "user", "parts": [SYSTEM_PROMPT]}, {"role": "user", "parts": [prompt]}],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        return json.loads(response.text)
    except Exception as e:
        print(f"Error in Gemini API: {e}")
        return _fallback_response()

def _fallback_response() -> dict:
    return {
        "is_job_related": False,
        "company_name": None,
        "role": None,
        "is_automation_receipt": False,
        "is_new_assessment_or_invitation": False,
        "status_summary": "Unknown",
        "expertise_level": "Generalist"
    }
