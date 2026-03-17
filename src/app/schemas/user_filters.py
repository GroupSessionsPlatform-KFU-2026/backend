from src.app.schemas.base import CommonListFilters


class UserFilters(CommonListFilters):
    username: str | None = None
    is_active: bool | None = None
