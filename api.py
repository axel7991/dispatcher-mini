
import os

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse, Gather

from main import graph
from database import create_tables, save_request


# =====================================================
# APPLICATION INITIALIZATION
# =====================================================

app = FastAPI(title="Dispatcher Mini API")

create_tables()


# =====================================================
# REQUEST MODELS
# =====================================================

class CustomerRequest(BaseModel):
    message: str


# =====================================================
# TWILIO HELPERS
# =====================================================

def twiml_response(voice_response):
    return Response(
        content=str(voice_response),
        media_type="application/xml"
    )


async def verify_twilio_request(request: Request):
    """
    Validate incoming Twilio webhooks using the auth token.
    Requires TWILIO_AUTH_TOKEN in the environment.
    """
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not auth_token:
        raise HTTPException(
            status_code=503,
            detail="Twilio webhook authentication is not configured"
        )

    form = await request.form()

    # Our public HTTPS address is used by Twilio.
    public_base_url = os.getenv(
        "PUBLIC_BASE_URL",
        "https://dispatcher.webwatchhq.com"
    ).rstrip("/")

    validation_url = public_base_url + request.url.path

    if request.url.query:
        validation_url += "?" + request.url.query

    signature = request.headers.get("X-Twilio-Signature", "")

    validator = RequestValidator(auth_token)

    if not validator.validate(
        validation_url,
        dict(form),
        signature
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid Twilio signature"
        )

    return form


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/")
def home():
    return {"message": "Dispatcher Mini is running!"}


# =====================================================
# TEXT DISPATCHER
# =====================================================

@app.post("/dispatch")
def dispatch(request: CustomerRequest):

    result = graph.invoke({
        "message": request.message
    })

    save_request(
        result["message"],
        result["intent"],
        result["department"]
    )

    return {
        "status": "processed",
        "message": result["message"],
        "intent": result["intent"],
        "department": result["department"],
        "response": result.get("response", "")
    }


# =====================================================
# TWILIO VOICE — INCOMING CALL
# =====================================================

@app.post("/voice")
async def voice(request: Request):

    await verify_twilio_request(request)

    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="/voice/process",
        method="POST",
        speech_timeout="auto",
        language="en-US"
    )

    gather.say(
        "Welcome to Dispatcher Mini. "
        "Please tell me how I can help you today."
    )

    response.append(gather)

    response.say(
        "Sorry, I didn't hear anything. "
        "Please call again."
    )

    return twiml_response(response)


# =====================================================
# TWILIO VOICE — PROCESS CUSTOMER SPEECH
# =====================================================

@app.post("/voice/process")
async def process_voice(request: Request):

    form = await verify_twilio_request(request)

    speech_result = str(form.get("SpeechResult", "")).strip()

    response = VoiceResponse()

    if not speech_result:
        response.say(
            "Sorry, I could not understand your request. "
            "Please call again."
        )
        response.hangup()
        return twiml_response(response)

    try:
        result = graph.invoke({
            "message": speech_result
        })

        save_request(
            result["message"],
            result["intent"],
            result["department"]
        )

        ai_response = result.get(
            "response",
            "Your request has been received."
        )

        response.say(ai_response)
        response.say(
            "Thank you for calling Dispatcher Mini. Goodbye."
        )
        response.hangup()

    except Exception:
        # Avoid exposing internal errors to callers.
        response.say(
            "Sorry, our automated assistant is temporarily "
            "unavailable. Please try again later."
        )
        response.hangup()

    return twiml_response(response)
