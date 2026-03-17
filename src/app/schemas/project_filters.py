from .base import CommonListFilters


class ProjectFilters(CommonListFilters):
    owner_id: int | None = None
    is_archived: bool | None = None
    title: str | None = None
