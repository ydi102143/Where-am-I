from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reflections: Mapped[list["Reflection"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    why: Mapped[str] = mapped_column(Text, default="")
    kgi: Mapped[str] = mapped_column(String(200), default="")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    area: Mapped[str] = mapped_column(String(50), default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="goals")
    tasks: Mapped[list["Task"]] = relationship(back_populates="goal", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    impact: Mapped[int] = mapped_column(Integer, default=1)
    effort_min: Mapped[int] = mapped_column(Integer, default=30)
    due: Mapped[date | None] = mapped_column(Date, nullable=True)
    parent_task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal: Mapped["Goal"] = relationship(back_populates="tasks")

class Reflection(Base):
    __tablename__ = "reflections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    text: Mapped[str] = mapped_column(Text, default="")
    mood: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="reflections")

class Suggestion(Base):
    __tablename__ = "suggestions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    type: Mapped[str] = mapped_column(String(20))
    content_json: Mapped[str] = mapped_column(Text)

class Integration(Base):
    __tablename__ = "integrations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(50))
    key:  Mapped[str] = mapped_column(String(50), default="default")
    value: Mapped[str] = mapped_column(Text)
