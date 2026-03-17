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

from typing import TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, Relationship
from datetime import datetime
from .base import Base

if TYPE_CHECKING:
    from .room import Room

class PomodoroSessionBase(Base):
    work_duration: int
    short_break_duration: int
    long_break_duration: int
    cycles_before_long: int
    current_phase: str
    completed_cycles: int = 0
    is_running: bool = False

class PomodoroSessionPublic(PomodoroSessionBase):
    id: int
    room_id: UUID

class PomodoroSessionCreate(PomodoroSessionBase):
    room_id: UUID

class PomodoroSessionUpdate(PomodoroSessionBase):
    current_phase: str | None = None
    completed_cycles: int | None = None
    is_running: bool | None = None
    phase_ends_at: datetime | None = None
    session_ends_at: datetime | None = None

class PomodoroSession(PomodoroSessionPublic, table=True):
    __tablename__ = "pomodorosession"
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key="room.id")
    phase_ends_at: datetime | None = None
    session_ends_at: datetime | None = None
    last_updated_at: datetime | None = None

    room: "Room" = Relationship(back_populates="pomodoro_sessions")