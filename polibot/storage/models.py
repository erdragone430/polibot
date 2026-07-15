from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(255))
    course: Mapped[str] = mapped_column(String(255))
    topic: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class StudentError(Base):
    __tablename__ = "student_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(String(255))
    exercise_id: Mapped[str] = mapped_column(String(255))
    step_index: Mapped[int] = mapped_column(Integer)
    skill_type: Mapped[str] = mapped_column(String(255))
    error_message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
