from datetime import datetime, timedelta, timezone
from enum import IntEnum
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field

from src.app.core.settings import settings

from .base import BaseModel


class EmailAction(IntEnum):
    VERIFY_ACCOUNT = 0
    CHANGE_PASSWORD = 1


class EmailNotification(BaseModel, table=True):
    __tablename__ = 'email_notification'

    code: UUID = Field(
        default_factory=uuid4,
        index=True,
        unique=True,
        nullable=False,
    )
    user_id: UUID = Field(
        foreign_key='user.id',
        index=True,
        nullable=False,
    )
    action: EmailAction = Field(nullable=False)
    expired_at: datetime = Field(
        default_factory=lambda: (
            datetime.now(timezone.utc)
            + timedelta(seconds=settings.email.notification_lifetime_seconds)
        ),
        nullable=False,
        sa_type=TIMESTAMP(timezone=True),  # type: ignore
    )
    is_used: bool = Field(default=False, nullable=False)
