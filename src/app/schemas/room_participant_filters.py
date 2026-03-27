from uuid import UUID

from src.app.schemas.base import CommonListFilters


class RoomParticipantFilters(CommonListFilters):
    user_id: UUID | None = None
    role: str | None = None
    is_kicked: bool | None = None
