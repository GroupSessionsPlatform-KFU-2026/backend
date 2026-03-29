from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .board_element import BoardElement
    from .chat_message import ChatMessage
    from .pomodoro_session import PomodoroSession
    from .project import Project
    from .room_participant import RoomParticipant
    from .user import User


class RoomStatus(StrEnum):
    ACTIVE = 'active'
    ENDED = 'ended'


class RoomBase(SQLModel):
    title: str
    max_participants: int


class RoomPublic(BaseModel, RoomBase):
    project_id: UUID
    creator_id: UUID
    room_code: str
    ended_at: datetime | None = None
    status: RoomStatus


class RoomCreate(RoomBase):
    project_id: UUID
    creator_id: UUID


class RoomUpdate(RoomBase):
    pass


class Room(RoomPublic, table=True):
    __tablename__ = 'room'

    project: 'Project' = Relationship(back_populates='rooms')
    creator: 'User' = Relationship(back_populates='created_rooms')
    participants: list['RoomParticipant'] = Relationship(back_populates='room')
    messages: list['ChatMessage'] = Relationship(back_populates='room')
    board_elements: list['BoardElement'] = Relationship(back_populates='room')
    pomodoro_sessions: list['PomodoroSession'] = Relationship(back_populates='room')
