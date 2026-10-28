
import os

from fastapi import FastAPI, Request, HTTPException
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
    """Return TwiML XML to Twilio."""
    return Response(
        content=str(voice_response),
        media_type="application/xml"
    )


async def verify_twilio_request(request: Request):
    """
    Validate Twilio webhook signatures for GET and POST.

    Diagnostic messages identify authentication failures
    without logging secrets, signatures, or customer data.
    """

    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not auth_token:
        print(
            "TWILIO_DIAGNOSTIC: auth_token_not_configured",
            flush=True
        )
        raise HTTPException(
            status_code=503,
            detail="Twilio webhook authentication is not configured"
        )

    public_base_url = os.getenv("PUBLIC_BASE_URL")

    if not public_base_url:
        print(
            "TWILIO_DIAGNOSTIC: public_base_url_not_configured",
            flush=True
        )
        raise HTTPException(
            status_code=503,
            detail="Public webhook URL is not configured"
        )

    public_base_url = public_base_url.rstrip("/")

    validation_url = public_base_url + request.url.path

    if request.url.query:
        validation_url += "?" + request.url.query

    signature = request.headers.get(
        "X-Twilio-Signature", ""
    )

    if not signature:
        print(
            "TWILIO_DIAGNOSTIC: missing_signature",
            flush=True
        )
        raise HTTPException(
            status_code=403,
            detail="Missing Twilio signature"
        )

    validator = RequestValidator(auth_token)

    if request.method == "GET":
        # Query parameters are included in validation_url.
        parameters = {}

    elif request.method == "POST":
        content_type = request.headers.get(
            "content-type", ""
        ).lower()

        if "application/x-www-form-urlencoded" not in content_type:
            print(
                "TWILIO_DIAGNOSTIC: unsupported_content_type",
                flush=True
            )
            raise HTTPException(
                status_code=415,
                detail="Unsupported webhook content type"
            )

        form = await request.form()
        parameters = dict(form)

    else:
        raise HTTPException(
            status_code=405,
            detail="Method not allowed"
        )

    if not validator.validate(
        validation_url,
        parameters,
        signature
    ):
        print(
            "TWILIO_DIAGNOSTIC: invalid_signature",
            flush=True
        )
        raise HTTPException(
            status_code=403,
            detail="Invalid Twilio signature"
        )

    print(
        "TWILIO_DIAGNOSTIC: signature_valid",
        flush=True
    )

    return parameters


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/")
def home():
    return {
        "message": "Dispatcher Mini is running!"
    }


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

@app.api_route("/voice", methods=["GET", "POST"])
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

    speech_result = str(
        form.get("SpeechResult", "")
    ).strip()

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

        response.say(str(ai_response))

        response.say(
            "Thank you for calling Dispatcher Mini. Goodbye."
        )

        response.hangup()

    except Exception:
        # Avoid exposing internal errors to callers.
        print(
            "TWILIO_DIAGNOSTIC: agent_processing_failed",
            flush=True
        )

        response.say(
            "Sorry, our automated assistant is temporarily "
            "unavailable. Please try again later."
        )
        response.hangup()

    return twiml_response(response)
