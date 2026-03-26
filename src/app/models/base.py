from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=TIMESTAMP(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={'onupdate': lambda: datetime.now(timezone.utc)},
        sa_type=TIMESTAMP(timezone=True),
    )
