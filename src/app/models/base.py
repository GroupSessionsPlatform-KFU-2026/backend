from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, SQLModel

class Base(SQLModel):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"onupdate": datetime.now}
    )