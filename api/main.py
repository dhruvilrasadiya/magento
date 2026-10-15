import os
import uvicorn
import mongoengine
from fastapi import FastAPI
from dotenv import load_dotenv
from routes.chat import chat_router
from utils import initialize_collections
from routes.sessions import session_router
from routes.authentication import auth_router
from fastapi.middleware.cors import CORSMiddleware
from routes.user import initialize_default_admin, user_router

load_dotenv()
mongoengine.connect(
    db=os.environ["MONGODB_DATABASE"],
    username=os.environ["MONGODB_USERNAME"],
    password=os.environ["MONGODB_PASSWORD"],
    host=os.environ["MONGODB_HOST"],
    port=int(os.environ["MONGODB_PORT"]),
)

app = FastAPI(title="Magento-bot API", version="1.0.0")

initialize_default_admin()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    # allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("Here 1")
initialize_collections()
print("Here 2")

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/users", tags=["User Management"])
app.include_router(chat_router, prefix="/chat", tags=["Chat Query"])
app.include_router(session_router, prefix="/session", tags=["Session Management"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
