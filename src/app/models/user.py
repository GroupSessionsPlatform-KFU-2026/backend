# from datetime import datetime
# from sqlmodel import SQLModel, Field

# class User(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     email: str = Field(index=True)
#     username: str = Field(index=True)
#     password_hash: str
#     avatar_url: str | None = None
#     created_at: datetime
#     last_login_at: datetime | None = None
#     is_active: bool


from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship
from datetime import datetime
from .base import Base

if TYPE_CHECKING:
    from .project import Project
    from .room import Room
    from .room_participant import RoomParticipant
    from .chat_message import ChatMessage
    from .board_element import BoardElement
    from .board_element_comment import BoardElementComment

class UserBase(Base):
    email: str = Field(index=True)
    username: str = Field(index=True)
    avatar_url: str | None = None
    is_active: bool = True

class UserPublic(UserBase):
    id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    email: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    is_active: bool | None = None

class User(UserPublic, table=True):
    __tablename__ = "user"                  
    id: int | None = Field(default=None, primary_key=True)
    password_hash: str
    last_login_at: datetime | None = None

    projects: list["Project"] = Relationship(back_populates="owner")
    created_rooms: list["Room"] = Relationship(back_populates="creator")
    participations: list["RoomParticipant"] = Relationship(back_populates="user")
    sent_messages: list["ChatMessage"] = Relationship(back_populates="sender")
    board_elements: list["BoardElement"] = Relationship(back_populates="author")
    comments: list["BoardElementComment"] = Relationship(back_populates="author")