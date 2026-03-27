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
from src.app.schemas.board_element_comment_filters import BoardElementCommentFilters


class BoardElementCommentService:
    __repository: BoardElementCommentRepository

    def __init__(self, repository: BoardElementCommentRepositoryDep):
        self.__repository = repository

    async def get_comments(
        self,
        element_id: UUID,
        filters: BoardElementCommentFilters,
    ) -> Sequence[BoardElementComment]:
        comments = await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )
        return [
            comment for comment in comments if comment.board_element_id == element_id
        ]

    async def create_comment(
        self,
        element_id: UUID,
        comment_create: BoardElementCommentCreate,
    ) -> BoardElementComment:
        comment = BoardElementComment(
            **comment_create.model_dump(),
            board_element_id=element_id,
            is_deleted=False,
        )
        return await self.__repository.save(comment)

    async def get_comment_in_element(
        self,
        element_id: UUID,
        comment_id: UUID,
    ) -> Optional[BoardElementComment]:
        comment = await self.__repository.get(comment_id)
        if comment is None:
            return None
        if comment.board_element_id != element_id:
            return None
        return comment

    async def update_comment(
        self,
        element_id: UUID,
        comment_id: UUID,
        comment_update: BoardElementCommentUpdate,
    ) -> Optional[BoardElementComment]:
        comment = await self.__repository.get(comment_id)
        if comment is None:
            return None
        if comment.board_element_id != element_id:
            return None
        return await self.__repository.update(comment_id, comment_update)

    async def delete_comment(
        self,
        element_id: UUID,
        comment_id: UUID,
    ) -> Optional[BoardElementComment]:
        comment = await self.__repository.get(comment_id)
        if comment is None:
            return None
        if comment.board_element_id != element_id:
            return None

        comment.is_deleted = True
        return await self.__repository.save(comment)
