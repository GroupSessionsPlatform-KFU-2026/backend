from src.app.schemas.base import CommonListFilters


class UserFilters(CommonListFilters):
    email: str | None = None
    username: str | None = None
    is_active: bool | None = None
