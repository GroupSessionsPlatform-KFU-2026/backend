# from datetime import datetime
# from uuid import UUID, uuid4
# from sqlmodel import SQLModel, Field

# class PomodoroSession(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     room_id: UUID = Field(foreign_key="room.id")
#     work_duration: int
#     short_break_duration: int
#     long_break_duration: int
#     cycles_before_long: int
#     current_phase: str
#     completed_cycles: int
#     phase_ends_at: datetime
#     session_ends_at: datetime
#     is_running: bool
#     last_updated_at: datetime

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .room import Room


class PomodoroSessionBase(SQLModel):
    work_duration: int
    short_break_duration: int
    long_break_duration: int
    cycles_before_long: int
    current_phase: str
    completed_cycles: int = 0
    is_running: bool = False


class PomodoroSessionPublic(BaseModel, PomodoroSessionBase):
    id: int
    room_id: UUID


class PomodoroSessionCreate(PomodoroSessionBase):
    room_id: UUID


class PomodoroSessionUpdate(PomodoroSessionBase):
    work_duration: int | None = None
    short_break_duration: int | None = None
    current_phase: str | None = None
    completed_cycles: int | None = None
    is_running: bool | None = None
    phase_ends_at: datetime | None = None
    session_ends_at: datetime | None = None


class PomodoroSession(PomodoroSessionPublic, table=True):
    __tablename__ = 'pomodoro_session'
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key='room.id')
    phase_ends_at: datetime | None = None
    session_ends_at: datetime | None = None
    last_updated_at: datetime | None = None

    room: 'Room' = Relationship(back_populates='pomodoro_sessions')
