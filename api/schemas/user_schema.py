from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserIn(BaseModel):
    email:str
    username: str
    password: str
    role: str = Field(..., pattern="^(admin|supervisor)$")


class UserOut(BaseModel):
    id: str
    email:str
    username: str
    role: str
    created_at: datetime

class PaginatedUserResponse(BaseModel):
    total: int
    users: list[UserOut]

class UserLogin(BaseModel):
    username: str
    password: str


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class ForgetPasswordRequest(BaseModel):
    email: str
    

class resatPassword(BaseModel):
    token: str
    new_password: str

class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    role: Optional[str]

class DeleteUserRequest(BaseModel):
    user_ids: List[str]