from pydantic import BaseModel


class CommonListFilters(BaseModel):
    offset: int = 0
    limit: int = 10
