from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .room import Room
    from .user import User


class RoomParticipantBase(SQLModel):
    room_id: UUID
    user_id: UUID


class RoomParticipantPublic(BaseModel, RoomParticipantBase):
    role: str
    joined_at: datetime | None = Field(
        default=None,
        sa_type=TIMESTAMP(timezone=True),
    )
    left_at: datetime | None = Field(
        default=None,
        sa_type=TIMESTAMP(timezone=True),
    )
    is_kicked: bool


class RoomParticipantCreate(RoomParticipantBase):
    pass


class RoomParticipantUpdate(RoomParticipantBase):
    pass


class RoomParticipant(RoomParticipantPublic, table=True):
    __tablename__ = 'room_participant'

    room_id: UUID = Field(foreign_key='room.id', nullable=False)
    user_id: UUID = Field(foreign_key='user.id', nullable=False)

    room: 'Room' = Relationship(back_populates='participants')
    user: 'User' = Relationship(back_populates='participations')
