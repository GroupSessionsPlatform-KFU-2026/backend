from collections.abc import Sequence
from typing import TypeVar

T = TypeVar('T')


def build_paginated_response(
    results: Sequence[T],
    count: int,
    page: int,
    page_size: int,
) -> dict[str, object]:
    return {
        'count': count,
        'page': page,
        'page_size': page_size,
        'results': results,
    }
