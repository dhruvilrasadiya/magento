import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from mongoengine.errors import DoesNotExist
from fastapi.responses import StreamingResponse
from agentic_ai.utils.llm_utils import LLMConfig
from database.chat import ChatSession, ChatMessage
from agentic_ai.utils.email_config import EmailConfig
from agentic_ai.orchestrator.graph import AgentOrchestrator
from schemas.message_schema import ChatResponse, ChatRequest
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

chat_router = APIRouter()
llm_config = LLMConfig()
email_config = EmailConfig.from_env()
orchestrator = AgentOrchestrator(llm_config, email_config.to_dict())
client = OpenAI()
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_EMAIL = os.getenv("EMAIL_FROM")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")


@chat_router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest, background_tasks: BackgroundTasks):
    try:
        session_id = request.session_id

        # 1. Fetch session
        session = ChatSession.objects(session_id=session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # 2. Check if this is the first user message
        #    (assumes you log each message in a Message collection)
        message_count = ChatMessage.objects(session_id=session_id).count()
        if message_count == 0:
            try:
                print("Generating session title...")
                prompt = (
                    "Summarize this user query as a short session title:\n\n"
                    f"{request.query}"
                )
                ai_response = client.chat.completions.create(
                    model=request.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an assistant that generates short, clear session titles.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=20,
                )

                session_title = ai_response.choices[0].message.content.strip()

                # Save the session title to the database
                session.name = session_title
                session.save()  # Use save() instead of update()

                print(f"Session title generated and saved: {session_title}")
            except Exception as e:
                print("Failed to generate or save session title:", e)
        else:
            session_title = (
                session.name
            )  # Use the existing session name for subsequent queries

        print(
            f"[INFO] auto send email: {request.auto_send_email}, type: {type(request.auto_send_email)}"
        )

        result = await orchestrator.process_query(
            query=request.query,
            model_name=request.model_name,
            session_id=session_id,
            language=request.language,
            auto_send_email=request.auto_send_email,
        )

        new = {"metadata": {}}
        # Always include the session name in the metadata
        new["metadata"]["email_output"] = result.get("email_output", {})
        new["metadata"]["inbox_output"] = result.get("inbox_output", {})


        # Store message in database asynchronously
        message_id = store_message(
            session_id=session_id,
            metadata=new.get("metadata", {}),
            message=request.query,
            response=result["response"],
        )
        response = ChatResponse(
            response=result["response"],
            session_id=session_id,
            metadata=new.get("metadata", {}),
            timestamp=datetime.now(),
            name=session_title,
            message_id=str(message_id),
        )


        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/stream")
async def stream_query(request: ChatRequest):
    session_id = request.session_id

    async def event_generator():
        try:
            async for chunk in orchestrator.process_stream(
                query=request.query,
                model_name=request.model_name,
                session_id=session_id,
            ):
                # Yield each chunk as a properly formatted Server-Sent Event
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        yield {"final": True, "message": "This is the final part of the stream"}

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def store_message(
    session_id: str, message: str, response: str, metadata: Dict[str, Any] = {}
):
    """Store chat message using MongoEngine."""
    try:
        session = ChatSession.objects.get(session_id=session_id)

        # Create a new ChatMessage
        chat_msg = ChatMessage(
            session_id=session_id,
            message=message,
            response=response,
            metadata=metadata,
            timestamp=datetime.now(),
        )
        chat_msg.save()

        # Append to session and update last activity
        session.update(push__messages=chat_msg, set__last_activity=datetime.now())
        return chat_msg.id

    except DoesNotExist:
        print(f"Session with ID {session_id} not found. Cannot store message.")
    except Exception as e:
        print(f"Error storing message: {str(e)}")


class EmailData(BaseModel):
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []
    subject: str
    body: str
    send_now: bool
    session_id: str
    message_id: str


class EmailRequest(BaseModel):
    email_data: EmailData


# Helper function to send email
def send_email(
    from_email: str,
    from_password: str,
    to_emails: List[str],
    subject: str,
    body: str,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
) -> bool:
    try:
        # Construct email
        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = ", ".join(to_emails)
        message["Subject"] = subject

        if cc_emails:
            message["Cc"] = ", ".join(cc_emails)

        message.attach(MIMEText(body, "plain"))

        recipients = to_emails.copy()
        if cc_emails:
            recipients.extend(cc_emails)
        if bcc_emails:
            recipients.extend(bcc_emails)

        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(from_email, from_password)
        server.sendmail(from_email, recipients, message.as_string())
        server.quit()

        print(f"[SUCCESS] Email sent to {', '.join(recipients)}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False


def update_send_now_flag(session_id: str, message: str) -> bool:
    try:
        doc = ChatMessage.objects.get(id=message)
        doc.metadata["email_output"]["email_data"]["send_now"] = True
        doc.save()
        return True
    except DoesNotExist:
        print(f"[ERROR] ChatMessage not found for session_id={session_id}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to update send_now flag: {e}")
        return False


# API endpoint
@chat_router.post("/send-email")
def send_email_api(request: EmailRequest):
    email_data = request.email_data

    if email_data.send_now:
        success = send_email(
            from_email=SMTP_EMAIL,
            from_password=SMTP_PASSWORD,
            to_emails=email_data.to,
            subject=email_data.subject,
            body=email_data.body,
            cc_emails=email_data.cc,
            bcc_emails=email_data.bcc,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email")
        updated = update_send_now_flag(
            session_id=email_data.session_id,
            message=email_data.message_id,
        )

        if not updated:
            raise HTTPException(
                status_code=500, detail="Failed to update send_now flag in DB"
            )

        return {
            "message": "Email sent and metadata updated",
            "sent_at": datetime.utcnow(),
        }

    return {"message": "Email not sent because send_now is False"}
