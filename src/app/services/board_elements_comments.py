from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    BoardElementCommentRepository,
    BoardElementCommentRepositoryDep,
)
from src.app.models.board_element_comment import (
    BoardElementComment,
    BoardElementCommentCreate,
    BoardElementCommentUpdate,
)
from src.app.schemas.board_element_comment_filters import BoardCommentFilters


class BoardElementCommentService:
    __repository: BoardElementCommentRepository

    def __init__(self, repository: BoardElementCommentRepositoryDep):
        self.__repository = repository

    async def get_comments(
        self, filters: BoardCommentFilters
    ) -> Sequence[BoardElementComment]:
        return await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_comment(
        self, comment_create: BoardElementCommentCreate
    ) -> BoardElementComment:
        comment_dump = comment_create.model_dump()
        comment = BoardElementComment(
            **comment_dump,
            is_deleted=False,
        )
        return await self.__repository.save(comment)

    async def update_comment(
        self, comment_update: BoardElementCommentUpdate, comment_id: UUID
    ) -> Optional[BoardElementComment]:
        return await self.__repository.update(comment_id, comment_update)

    async def delete_comment(
        self, comment_id: UUID
    ) -> Optional[BoardElementComment]:
        comment = await self.__repository.get(comment_id)
        if comment is None:
            return None

        comment.is_deleted = True
        return await self.__repository.save(comment)