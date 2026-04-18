from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .room import Room


class PomodoroPhase(StrEnum):
    WORK = 'work'
    SHORT_BREAK = 'short_break'
    LONG_BREAK = 'long_break'


class PomodoroSessionBase(SQLModel):
    work_duration: int
    short_break_duration: int
    long_break_duration: int
    cycles_before_long: int


class PomodoroSessionPublic(BaseModel, PomodoroSessionBase):
    room_id: UUID
    current_phase: PomodoroPhase
    completed_cycles: int
    phase_ends_at: datetime | None = Field(
        default=None,
        sa_type=TIMESTAMP(timezone=True),
    )
    session_ends_at: datetime | None = Field(
        default=None,
        sa_type=TIMESTAMP(timezone=True),
    )
    is_running: bool


class PomodoroSessionCreate(PomodoroSessionBase):
    room_id: UUID


class PomodoroSessionUpdate(PomodoroSessionBase):
    pass


class PomodoroSession(PomodoroSessionPublic, table=True):
    __tablename__ = 'pomodoro_session'

    room_id: UUID = Field(foreign_key='room.id', nullable=False)

    room: 'Room' = Relationship(back_populates='pomodoro_sessions')
