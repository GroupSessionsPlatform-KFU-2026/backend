from datetime import datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field

from src.app.models.base import BaseModel


class RefreshSession(BaseModel, table=True):
    __tablename__ = 'refresh_sessions'

    user_id: UUID = Field(
        foreign_key='user.id',
        nullable=False,
        index=True,
    )
    jti: str = Field(
        nullable=False,
        unique=True,
        index=True,
        max_length=255,
    )
    expires_at: datetime = Field(
        nullable=False,
        sa_type=TIMESTAMP(timezone=True),
    )
    is_revoked: bool = Field(
        default=False,
        nullable=False,
    )
