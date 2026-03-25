from src.app.schemas.base import CommonListFilters

class TagFilters(CommonListFilters):
    name: str | None = None