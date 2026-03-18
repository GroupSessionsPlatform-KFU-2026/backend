from uuid import UUID

from src.app.schemas.base import CommonListFilters


class ProjectTagFilters(CommonListFilters):
    project_id: UUID | None = None
    tag_id: UUID | None = None
    is_active: bool | None = None
