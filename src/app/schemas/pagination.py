from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class PaginationInfo(BaseModel):
    page: int
    pages_num: int
    total: int


class PaginatedResponse(BaseModel, Generic[T]):
    info: PaginationInfo
    items: list[T]


def build_paginated_response(
    items: list[T],
    total: int,
    offset: int,
    limit: int,
) -> PaginatedResponse[T]:
    page = offset // limit + 1 if limit else 1
    pages_num = ceil(total / limit) if limit else 1

    return PaginatedResponse[T](
        info=PaginationInfo(
            page=page,
            pages_num=pages_num,
            total=total,
        ),
        items=items,
    )
