from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from typing import Dict, Optional
import os
from dotenv import load_dotenv
from models import FormFillRequest, FormFillResponse, ChatSession
from form_agent import FormFillingAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Form Filling Agent API",
    description="API for automated form filling via chat apps",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize form filling agent
agent = FormFillingAgent()

# Request/Response models
class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    user_id: str

class SubmitFormRequest(BaseModel):
    session_id: str
    user_id: str

class WebhookRequest(BaseModel):
    user_id: str
    message: str
    chat_platform: str
    webhook_url: Optional[str] = None

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Form Filling Agent API is running"}

@app.post("/fill_form", response_model=FormFillResponse)
async def fill_form(request: FormFillRequest):
    """
    Start form filling process for a given URL
    """
    try:
        logger.info(f"Received form fill request for user {request.user_id}: {request.form_url}")
        response = agent.process_form_request(request)
        return response
    except Exception as e:
        logger.error(f"Error processing form fill request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=FormFillResponse)
async def handle_chat_message(request: ChatMessageRequest):
    """
    Handle chat message from user (providing missing information)
    """
    try:
        logger.info(f"Received chat message for session {request.session_id}")
        response = agent.handle_user_response(request.session_id, request.message)
        return response
    except Exception as e:
        logger.error(f"Error handling chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit", response_model=FormFillResponse)
async def submit_form(request: SubmitFormRequest):
    """
    Submit a filled form
    """
    try:
        logger.info(f"Received submit request for session {request.session_id}")
        response = agent.submit_form(request.session_id)
        return response
    except Exception as e:
        logger.error(f"Error submitting form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}")
async def get_session_status(session_id: str):
    """
    Get current status of a session
    """
    try:
        session = agent.get_session_status(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "form_url": session.form_url,
            "status": session.status,
            "missing_fields": session.missing_fields,
            "collected_data_count": len(session.collected_data),
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}/stats")
async def get_user_stats(user_id: str):
    """
    Get user statistics
    """
    try:
        stats = agent.get_user_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook_handler(request: WebhookRequest, background_tasks: BackgroundTasks):
    """
    Handle webhook requests from chat platforms
    This endpoint processes messages from WhatsApp, iMessage, etc.
    """
    try:
        logger.info(f"Received webhook from {request.chat_platform} for user {request.user_id}")
        
        # Check if message contains a URL
        message = request.message.strip()
        if any(url_indicator in message.lower() for url_indicator in ['http', 'www.', '.com', '.org', '.net']):
            # Extract URL from message
            url = extract_url_from_message(message)
            if url:
                # Start form filling process
                form_request = FormFillRequest(
                    user_id=request.user_id,
                    form_url=url,
                    chat_platform=request.chat_platform,
                    webhook_url=request.webhook_url
                )
                
                # Process in background
                background_tasks.add_task(process_webhook_form_request, form_request)
                
                return {"message": "Processing form URL, please wait..."}
        
        # If no URL found, treat as regular chat message
        # For now, return simple response
        return {"message": "Please send me a form URL to fill out automatically."}
        
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def extract_url_from_message(message: str) -> Optional[str]:
    """Extract URL from chat message"""
    import re
    
    # Simple URL regex pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    urls = re.findall(url_pattern, message)
    if urls:
        return urls[0]
    
    # Also check for www. patterns
    www_pattern = r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    www_urls = re.findall(www_pattern, message)
    if www_urls:
        return f"https://{www_urls[0]}"
    
    return None

async def process_webhook_form_request(request: FormFillRequest):
    """Process form request from webhook in background"""
    try:
        response = agent.process_form_request(request)
        
        # If webhook URL is provided, send response back
        if request.webhook_url:
            await send_webhook_response(request.webhook_url, response)
        
        logger.info(f"Completed webhook form processing for user {request.user_id}")
        
    except Exception as e:
        logger.error(f"Error processing webhook form request: {str(e)}")

async def send_webhook_response(webhook_url: str, response: FormFillResponse):
    """Send response back to chat platform via webhook"""
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=response.dict())
        
        logger.info(f"Sent webhook response to {webhook_url}")
        
    except Exception as e:
        logger.error(f"Error sending webhook response: {str(e)}")

# Chat platform specific endpoints

@app.post("/whatsapp")
async def whatsapp_webhook(request: dict):
    """
    Handle WhatsApp webhook specifically
    """
    try:
        # Extract WhatsApp message data
        # This is a simplified example - real WhatsApp webhook handling would be more complex
        
        if "messages" in request:
            message = request["messages"][0]
            user_id = message.get("from", "")
            text = message.get("text", {}).get("body", "")
            
            webhook_request = WebhookRequest(
                user_id=user_id,
                message=text,
                chat_platform="whatsapp"
            )
            
            return await webhook_handler(webhook_request, BackgroundTasks())
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/telegram")
async def telegram_webhook(request: dict):
    """
    Handle Telegram webhook specifically
    """
    try:
        # Extract Telegram message data
        if "message" in request:
            message = request["message"]
            user_id = str(message.get("from", {}).get("id", ""))
            text = message.get("text", "")
            
            webhook_request = WebhookRequest(
                user_id=user_id,
                message=text,
                chat_platform="telegram"
            )
            
            return await webhook_handler(webhook_request, BackgroundTasks())
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error handling Telegram webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the server
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)