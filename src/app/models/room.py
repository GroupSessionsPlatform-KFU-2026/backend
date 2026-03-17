# from datetime import datetime
# from sqlmodel import SQLModel, Field
# from uuid import UUID, uuid4

# class Room(SQLModel, table=True):
#     id: UUID = Field(default_factory=uuid4, primary_key=True)
#     project_id: int = Field(foreign_key="project.id")
#     creator_id: int = Field(foreign_key="user.id")
#     title: str
#     room_code: str = Field(index=True)
#     created_at: datetime
#     ended_at: datetime | None = None
#     status: str

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .board_element import BoardElement
    from .chat_message import ChatMessage
    from .pomodoro_session import PomodoroSession
    from .project import Project
    from .room_participant import RoomParticipant
    from .user import User


class RoomBase(SQLModel):
    title: str
    room_code: str = Field(index=True)
    status: str


class RoomPublic(BaseModel, RoomBase):
    id: UUID
    project_id: int
    creator_id: int


class RoomCreate(RoomBase):
    project_id: int
    creator_id: int


class RoomUpdate(RoomBase):
    title: str | None = None
    room_code: str | None = None
    status: str | None = None


class Room(RoomPublic, table=True):
    __tablename__ = 'room'
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: int = Field(foreign_key='project.id')
    creator_id: int = Field(foreign_key='user.id')
    ended_at: datetime | None = None

    project: 'Project' = Relationship(back_populates='rooms')
    creator: 'User' = Relationship(back_populates='created_rooms')
    participants: list['RoomParticipant'] = Relationship(back_populates='room')
    messages: list['ChatMessage'] = Relationship(back_populates='room')
    board_elements: list['BoardElement'] = Relationship(back_populates='room')
    pomodoro_sessions: list['PomodoroSession'] = Relationship(back_populates='room')
