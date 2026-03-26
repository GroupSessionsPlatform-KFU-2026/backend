from uuid import UUID

from .base import CommonListFilters


class ProjectFilters(CommonListFilters):
    owner_id: UUID | None = None
    is_archived: bool | None = None
    title: str | None = None
