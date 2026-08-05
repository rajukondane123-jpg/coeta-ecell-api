import os
import logging
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.genai import Client

# ---------------------------------------------------------
# 1. LOGGING & SYSTEM SETUP
# ---------------------------------------------------------
# This prints detailed color-coded server logs in your Termux window
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 2. GOOGLE API CONFIGURATION
# ---------------------------------------------------------
# IMPORTANT: Delete "PASTE_YOUR_AIzaSy_KEY_HERE" and paste your real key.
# A valid Google API key WILL ALWAYS start with "AIzaSy".
# Do not use tokens starting with "AQ." or you will get a quota of 0.
os.environ["GEMINI_API_KEY"] = "PASTE API KEY HERE"

client = Client()
document = None

# ---------------------------------------------------------
# 3. FASTAPI SERVER INITIALIZATION
# ---------------------------------------------------------
app = FastAPI(title="COETA E-Cell Backend API")
BOT_IS_ACTIVE = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# ---------------------------------------------------------
# 4. SYSTEM ROUTES & WIDGET CONTROLS
# ---------------------------------------------------------
@app.get("/")
def read_root():
    """Health check route to ensure the backend is running."""
    return {"status": "E-Cell Backend is live and running flawlessly!"}

@app.get("/admin/toggle")
def toggle_bot():
    global BOT_IS_ACTIVE
    BOT_IS_ACTIVE = not BOT_IS_ACTIVE
    status = "ONLINE" if BOT_IS_ACTIVE else "OFFLINE"
    logger.info(f"System Admin toggled bot status to: {status}")
    return {"message": f"Bot is now {status}"}

@app.get("/widget.js")
def serve_widget():
    if not BOT_IS_ACTIVE:
        return Response(content="console.log('Bot offline');", media_type="application/javascript")
    js_code = "console.log('Bot is active! Ready to load chat UI.');"
    return Response(content=js_code, media_type="application/javascript")

# ---------------------------------------------------------
# 5. ADVANCED CHAT PROCESSOR WITH SMART ERROR HANDLING
# ---------------------------------------------------------
@app.post("/chat")
def chat_with_bot(request: ChatRequest):
    if not BOT_IS_ACTIVE:
        return {"reply": "The E-Cell chatbot is currently offline for maintenance."}

    prompt = f"You are the official chatbot for the COETA E-Cell. Keep answers short. Question: {request.me>
    contents = [prompt]
    if document:
        contents.append(document)

    try:
        logger.info(f"Sending user message to Gemini: {request.message}")

        ai_response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=contents
        )

        logger.info("Successfully received AI response.")
        return {"reply": ai_response.text}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to fetch AI response: {error_msg}")

        # Smart error interception to diagnose the exact issue on the frontend
        if "limit: 0" in error_msg:
            return {"reply": "CRITICAL ERROR: Your API key quota is 0. You are using an invalid 'AQ.' token>
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {"reply": "Google API speed limit reached! Please wait exactly 60 seconds and try again.>
        elif "API_KEY_INVALID" in error_msg:
            return {"reply": "CRITICAL ERROR: Your API key is invalid or incomplete."}
        else:
            return {"reply": f"Unexpected System Error: {error_msg}"}
