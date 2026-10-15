# utils/password_utils.py
import bcrypt


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


#####################################    Vector DB Collection    ########################################################

import os, re
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client.http.models import VectorParams, Distance

load_dotenv()

embedding_model = OpenAIEmbeddings(
    model=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
    openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
)
EMBEDDING_DIM = len(embedding_model.embed_documents(["sample text"])[0])


QDRANT_HOST = os.environ.get("QDRANT_HOST", "")
QDRANT_PORT = os.environ.get("QDRANT_PORT", "")

COLLECTION_TO_QDRANT = {
    "order_data": {"host": QDRANT_HOST, "port": QDRANT_PORT},
    "product_data": {"host": QDRANT_HOST, "port": QDRANT_PORT},
    "pdf_data": {"host": QDRANT_HOST, "port": QDRANT_PORT},
    "crm_data": {"host": QDRANT_HOST, "port": QDRANT_PORT},
}


qdrant_clients = {}
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def initialize_collections():
    for collection_name in [
        "order_data",
        "product_data",
        "pdf_data",
        "customer_data",
        "analysis_data",
    ]:
        if not client.collection_exists(collection_name):
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM, distance=Distance.COSINE
                ),
            )


#####################################       Password      ########################################################


def is_valid_password(password: str) -> bool:
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)  # At least one uppercase
        and re.search(r"\d", password)  # At least one digit
        and re.search(
            r"[!@#$%^&*(),.?\":{}|<>]", password
        )  # At least one special character
    )


#####################################   Forgot Password   ########################################################

import smtplib, os
from jose import jwt
from dotenv import load_dotenv
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FORGOT_PASSWORD_SECRET = os.getenv(
    "FORGOT_PASSWORD_SECRET"
)  # Store securely (e.g., in .env)
ALGORITHM = os.getenv("ALGORITHM")


def create_reset_token(email: str) -> str:
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(minutes=10)}
    return jwt.encode(payload, FORGOT_PASSWORD_SECRET, algorithm=ALGORITHM)


def send_reset_email(to_email: str, reset_link: str, username: str):
    subject = "Reset Your Password"
    html_content = f"""
    <html>
        <body>
            <p>Hello {username},</p>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}">{reset_link}</a>
            <p>This link will expire in 10 minutes.</p>
        </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = to_email

    message.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, to_email, message.as_string())
        server.quit()
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")
