from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Auth ----------
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    user_id: int


# ---------- Chat ----------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # if omitted, a new session is started


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    agent_used: str
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    agent_used: str


# ---------- Reports ----------
class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    summary: Optional[str]
    created_at: datetime


class ReportDetailOut(ReportOut):
    extracted_text: Optional[str]


# ---------- Dashboard ----------
class SessionSummary(BaseModel):
    session_id: str
    last_message: str
    last_role: str
    message_count: int
    updated_at: datetime
