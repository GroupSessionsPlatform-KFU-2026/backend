from math import ceil
from typing import TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

from src.app.models.base import BaseModel as ProjectBaseModel

T = TypeVar('T', bound=ProjectBaseModel)


class PaginationInfo(BaseModel):
    page: int
    pages_num: int
    total: int


class PaginatedResponse(BaseModel, GenericModel[T]):
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
