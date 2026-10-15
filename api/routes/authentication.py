import os
from typing import Optional
from database.user import User
from dotenv import load_dotenv
from mongoengine import DoesNotExist
from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Header
from schemas.user_schema import UserLogin, ForgetPasswordRequest, resatPassword
from utils import hash_password, verify_password, create_reset_token, send_reset_email, is_valid_password

load_dotenv()

ACCESS_TOKEN_SECRET  = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"  
ACCESS_TOKEN_EXPIRE_MINUTES = 60
FORGOT_PASSWORD_SECRET = os.getenv("FORGOT_PASSWORD_SECRET")
FRONTEND_URL=os.getenv("FRONTEND_URL")
REFRESH_SECRET_KEY=os.getenv("REFRESH_SECRET_KEY")


def get_current_admin(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Token is not provided or invalid format")
    
    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, key=ACCESS_TOKEN_SECRET, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")

    user_id = payload.get("user_id")
    role = payload.get("role")

    if not user_id:
        raise HTTPException(status_code=401, detail="user_id missing in token")

    try:
        user = User.objects.get(id=user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="User is not available")

    if role != user.role:
        raise HTTPException(status_code=403, detail="Invalid role")

    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, ACCESS_TOKEN_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def verify_refresh_token(token: str):
    return jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

auth_router = APIRouter()


@auth_router.post("/refresh-token")
async def refresh_access_token(payload: dict):
    refresh_token = payload.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=403, detail="Refresh token missing")

    try:
        decoded = verify_refresh_token(refresh_token)
        user_id = decoded.get("user_id")
        role = decoded.get("role")

        if not user_id or not role:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
        
        if not User.objects.get(id=user_id):
            raise HTTPException(status_code=403, detail="User is not available")

        new_access_token = create_access_token({"user_id": user_id, "role": role})
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired refresh token")


@auth_router.post("/login")
async def login_user(credentials: UserLogin ):
    user = User.objects(username=credentials.username).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token_data = {"user_id": user.id, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {"detail": "Login successful", "token": access_token, "refresh_token" : refresh_token,
         "user_id": user.id, "role": user.role, "user_name": user.username, "email": user.email}


@auth_router.post("/forgot-password")
async def forgot_password(request: ForgetPasswordRequest, background_tasks: BackgroundTasks):
    try:
        valid = validate_email(request.email, check_deliverability=False)
        email = valid.email

        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email not registered")

        reset_token = create_reset_token(email=email)
        reset_link = f"{FRONTEND_URL}/login?reset-password&token={reset_token}"

        # Background task using smtplib
        background_tasks.add_task(send_reset_email, email, reset_link, user.username)

        return {"detail": "Reset email sent successfully"}
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email address")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.post("/reset-password")
async def reset_password(
    request: resatPassword
):
    try:
        if not FORGOT_PASSWORD_SECRET or not ALGORITHM:
            raise HTTPException(status_code=500, detail="Server configuration error")

        payload = jwt.decode(request.token, FORGOT_PASSWORD_SECRET, algorithms=[ALGORITHM])
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload")

        user = User.objects(email=email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if not is_valid_password(request.new_password):
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long, and include at least one uppercase letter, one special character, and one number."
            )

        user.password = hash_password(request.new_password)
        user.save()

        return {"detail": "Password reset successfully"}
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
