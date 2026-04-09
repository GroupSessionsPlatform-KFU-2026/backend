from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel
from .user_role import UserRoleLink

if TYPE_CHECKING:
    from .board_element import BoardElement
    from .board_element_comment import BoardElementComment
    from .chat_message import ChatMessage
    from .project import Project
    from .role import Role
    from .room import Room
    from .room_participant import RoomParticipant
    from .role import Role


class UserBase(SQLModel):
    email: str = Field(index=True)
    username: str = Field(index=True)
    avatar_url: str | None = None


class UserPublic(BaseModel, UserBase):
    last_login_at: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=TIMESTAMP(timezone=True),
    )
    is_active: bool
    is_verified: bool


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    email: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    is_active: bool | None = None


class User(UserPublic, table=True):
    __tablename__ = 'user'
    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('username', name='uq_user_username'),
    )
    password_hash: str
    is_verified: bool = Field(default=False, nullable=False)
    roles: list['Role'] = Relationship(
        back_populates='users',
        link_model=UserRoleLink,
    )
    projects: list['Project'] = Relationship(back_populates='owner')
    created_rooms: list['Room'] = Relationship(back_populates='creator')
    participations: list['RoomParticipant'] = Relationship(back_populates='user')
    sent_messages: list['ChatMessage'] = Relationship(back_populates='sender')
    board_elements: list['BoardElement'] = Relationship(back_populates='author')
    comments: list['BoardElementComment'] = Relationship(back_populates='author')
