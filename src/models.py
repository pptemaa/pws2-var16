"""Реляционная модель данных варианта 16 на SQLAlchemy."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс таблиц."""


class Agent(Base):
    """Агент, создающий вычислительные задачи."""

    __tablename__ = "agent"

    key: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)


class Task(Base):
    """Задача преобразования MP3 в WAV."""

    __tablename__ = "task"

    key: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    argument: Mapped[str] = mapped_column(Text, nullable=False)
    agent: Mapped[int] = mapped_column(ForeignKey("agent.key"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[str] = mapped_column(String, nullable=False)
    processed: Mapped[int] = mapped_column(Integer, nullable=False)
    launched: Mapped[int] = mapped_column(Integer, nullable=False)


class Feedback(Base):
    """Результат выполнения задачи."""

    __tablename__ = "feedback"

    key: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    failure: Mapped[str] = mapped_column(Text, nullable=False)
    task: Mapped[int] = mapped_column(ForeignKey("task.key"), nullable=False)
    cache_hit: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
