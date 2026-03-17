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

from typing import TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, Relationship
from datetime import datetime
from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .project import Project
    from .room_participant import RoomParticipant
    from .chat_message import ChatMessage
    from .board_element import BoardElement
    from .pomodoro_session import PomodoroSession

class RoomBase(Base):
    title: str
    room_code: str = Field(index=True)
    status: str

class RoomPublic(RoomBase):
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
    __tablename__ = "room"
    id: UUID = Field(default_factory=UUID, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    creator_id: int = Field(foreign_key="user.id")
    ended_at: datetime | None = None

    project: "Project" = Relationship(back_populates="rooms")
    creator: "User" = Relationship(back_populates="created_rooms")
    participants: list["RoomParticipant"] = Relationship(back_populates="room")
    messages: list["ChatMessage"] = Relationship(back_populates="room")
    board_elements: list["BoardElement"] = Relationship(back_populates="room")
    pomodoro_sessions: list["PomodoroSession"] = Relationship(back_populates="room")