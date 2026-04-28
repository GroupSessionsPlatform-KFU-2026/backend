from typing import Optional, Sequence
from uuid import UUID

from fastapi import HTTPException, status

from src.app.dependencies.repositories import (
    BoardElementRepository,
    BoardElementRepositoryDep,
)
from src.app.models.board_element import (
    BoardElement,
    BoardElementCreate,
    BoardElementUpdate,
)
from src.app.schemas.board_elements_filters import BoardElementFilters


class BoardElementService:
    __repository: BoardElementRepository

    def __init__(self, repository: BoardElementRepositoryDep):
        self.__repository = repository

    async def get_elements(
        self,
        room_id: UUID,
        filters: BoardElementFilters,
    ) -> Sequence[BoardElement]:
        return await self.__repository.fetch(
            filters=filters,
            extra_filters={
                'room_id': room_id,
            },
            offset=filters.offset,
            limit=filters.limit,
        )

    async def get_element_in_room(
        self,
        room_id: UUID,
        element_id: UUID,
    ) -> Optional[BoardElement]:
        return await self.__repository.get_one_by_filters(
            extra_filters={
                'room_id': room_id,
                'id': element_id,
            },
        )

    async def create_element(
        self,
        room_id: UUID,
        element_create: BoardElementCreate,
    ) -> BoardElement:
        element_dump = element_create.model_dump(exclude={'room_id'})
        element = BoardElement(
            **element_dump,
            room_id=room_id,
            is_deleted=False,
        )
        return await self.__repository.save(element)

    async def update_element(
        self,
        room_id: UUID,
        element_id: UUID,
        element_update: BoardElementUpdate,
    ) -> BoardElement:
        element = await self.get_element_in_room(room_id, element_id)

        if element is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Board element not found',
            )

        return await self.__repository.update(element.id, element_update)

    async def delete_element(
        self,
        room_id: UUID,
        element_id: UUID,
    ) -> BoardElement:
        element = await self.get_element_in_room(room_id, element_id)

        if element is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Board element not found',
            )

        element.is_deleted = True
        return await self.__repository.save(element)

    async def count_elements(
        self,
        room_id: UUID,
        filters: BoardElementFilters,
    ) -> int:
        return await self.__repository.count(
            filters=filters,
            extra_filters={'room_id': room_id},
        )
