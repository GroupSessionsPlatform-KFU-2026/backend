from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .room import Room


class PomodoroSessionBase(SQLModel):
    work_duration: int
    short_break_duration: int
    long_break_duration: int
    cycles_before_long: int


class PomodoroSessionPublic(BaseModel, PomodoroSessionBase):
    room_id: UUID
    current_phase: str
    completed_cycles: int
    phase_ends_at: datetime | None = None
    session_ends_at: datetime | None = None
    is_running: bool


class PomodoroSessionCreate(PomodoroSessionBase):
    room_id: UUID


class PomodoroSessionUpdate(PomodoroSessionBase):
    pass


class PomodoroSession(PomodoroSessionPublic, table=True):
    __tablename__ = 'pomodoro_session'

    room: 'Room' = Relationship(back_populates='pomodoro_sessions')
