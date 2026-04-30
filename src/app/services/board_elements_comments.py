from typing import Optional, Sequence
from uuid import UUID

from fastapi import HTTPException, status

from src.app.dependencies.repositories import (
    BoardElementCommentRepository,
    BoardElementCommentRepositoryDep,
    BoardElementRepository,
    BoardElementRepositoryDep,
)
from src.app.models.board_element import BoardElement
from src.app.models.board_element_comment import (
    BoardElementComment,
    BoardElementCommentCreate,
    BoardElementCommentUpdate,
)
from src.app.schemas.board_element_comment_filters import BoardElementCommentFilters


class BoardElementCommentService:
    __repository: BoardElementCommentRepository
    __board_element_repository: BoardElementRepository

    def __init__(
        self,
        repository: BoardElementCommentRepositoryDep,
        board_element_repository: BoardElementRepositoryDep,
    ):
        self.__repository = repository
        self.__board_element_repository = board_element_repository

    async def get_room_element(
        self,
        room_id: UUID,
        element_id: UUID,
    ) -> Optional[BoardElement]:
        return await self.__board_element_repository.get_one_by_filters(
            extra_filters={
                'room_id': room_id,
                'id': element_id,
            },
        )

    async def get_comments(
        self,
        room_id: UUID,
        element_id: UUID,
        filters: BoardElementCommentFilters,
    ) -> Sequence[BoardElementComment]:
        element = await self.get_room_element(room_id, element_id)
        if element is None:
            return []

        return await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
            extra_filters={'board_element_id': element_id},
        )

    async def create_comment(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_create: BoardElementCommentCreate,
    ) -> BoardElementComment:
        element = await self.get_room_element(room_id, element_id)

        if element is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Board element not found',
            )

        comment_dump = comment_create.model_dump(exclude={'board_element_id'})
        comment = BoardElementComment(
            **comment_dump,
            board_element_id=element_id,
            is_deleted=False,
        )
        return await self.__repository.save(comment)

    async def get_comment_in_element(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_id: UUID,
    ) -> BoardElementComment:
        element = await self.get_room_element(room_id, element_id)

        if element is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Board element not found',
            )

        comment = await self.__repository.get_one_by_filters(
            extra_filters={
                'id': comment_id,
                'board_element_id': element_id,
            },
        )

        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Comment not found',
            )

        return comment

    async def update_comment(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_id: UUID,
        comment_update: BoardElementCommentUpdate,
    ) -> BoardElementComment:
        comment = await self.get_comment_in_element(room_id, element_id, comment_id)
        return await self.__repository.update(comment.id, comment_update)

    async def delete_comment(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_id: UUID,
    ) -> BoardElementComment:
        comment = await self.get_comment_in_element(room_id, element_id, comment_id)

        comment.is_deleted = True
        return await self.__repository.save(comment)

    async def count_comments(
        self,
        room_id: UUID,
        element_id: UUID,
        filters: BoardElementCommentFilters,
    ) -> int:
        element = await self.get_room_element(room_id, element_id)
        if element is None:
            return 0

        return await self.__repository.count(
            filters=filters,
            extra_filters={'board_element_id': element_id},
        )
