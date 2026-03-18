from src.app.schemas.base import CommonListFilters


class ProjectTagFilters(CommonListFilters):
    project_id: int | None = None
    tag_id: int | None = None
    is_active: bool | None = None
