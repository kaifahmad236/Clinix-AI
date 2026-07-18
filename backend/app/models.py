from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chats = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")


class ChatMessage(Base):
    """One row per message (user or assistant), grouped by session_id so a
    dashboard can list distinct conversations."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    agent_used = Column(String, default="chat_agent")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")
