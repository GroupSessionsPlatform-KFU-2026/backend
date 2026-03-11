from typing import Annotated
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    username: str = Field(index=True)
    password_hash: str
    avatar_url: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None
    is_active: bool

class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    title: str
    description: str | None=None
    created_at: datetime
    updated_at: datetime | None = None
    is_archived: bool

class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    color: str
    description: str | None = None
    created_at: datetime


class ProjectTag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    tag_id: int = Field(foreign_key="tag.id")
    created_at: datetime
    is_active: bool


class Room(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    creator_id: int = Field(foreign_key="user.id")
    title: str
    room_code: str = Field(index=True)
    created_at: datetime
    ended_at: datetime | None = None
    status: str

class RoomParticipant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key="room.id")
    user_id: int = Field(foreign_key="user.id")
    role: str
    joined_at: datetime
    left_at: datetime | None = None
    is_kicked: bool


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key="room.id")
    sender_id: int = Field(foreign_key="user.id")
    content: str
    sent_at: datetime
    is_edited: bool


class BoardElement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key="room.id")
    author_id: int = Field(foreign_key="user.id")
    element_type: str
    data: str               
    created_at: datetime
    updated_at: datetime | None = None
    is_deleted: bool


class BoardElementComment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    board_element_id: int = Field(foreign_key="boardelement.id")
    author_id: int = Field(foreign_key="user.id")
    content: str
    is_deleted: bool
    created_at: datetime

class PomodoroSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key="room.id")
    work_duration: int
    short_break_duration: int
    long_break_duration: int
    cycles_before_long: int
    current_phase: str
    completed_cycles: int
    phase_ends_at: datetime
    session_ends_at: datetime
    is_running: bool
    last_updated_at: datetime

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]