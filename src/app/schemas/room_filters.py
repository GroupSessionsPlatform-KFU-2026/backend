from uuid import UUID

from .base import CommonListFilters


class RoomFilters(CommonListFilters):
    project_id: UUID | None = None
    creator_id: UUID | None = None
    status: str | None = None
    room_code: str | None = None
