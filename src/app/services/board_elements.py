from typing import Optional, Sequence
from uuid import UUID

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
        repository_filters = BoardElementFilters(
            author_id=filters.author_id,
            element_type=filters.element_type,
            is_deleted=filters.is_deleted,
            offset=filters.offset,
            limit=filters.limit,
        )
        elements = await self.__repository.fetch(
            filters=repository_filters,
            offset=repository_filters.offset,
            limit=repository_filters.limit,
        )
        return [element for element in elements if element.room_id == room_id]

    async def get_element_in_room(
        self,
        room_id: UUID,
        element_id: UUID,
    ) -> Optional[BoardElement]:
        element = await self.__repository.get(element_id)
        if element is None:
            return None
        if element.room_id != room_id:
            return None
        return element

    async def create_element(
        self,
        room_id: UUID,
        element_create: BoardElementCreate,
    ) -> BoardElement:
        element_dump = element_create.model_dump()
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
    ) -> Optional[BoardElement]:
        element = await self.__repository.get(element_id)
        if element is None:
            return None
        if element.room_id != room_id:
            return None
        return await self.__repository.update(element_id, element_update)

    async def delete_element(
        self,
        room_id: UUID,
        element_id: UUID,
    ) -> Optional[BoardElement]:
        element = await self.__repository.get(element_id)
        if element is None:
            return None
        if element.room_id != room_id:
            return None

        element.is_deleted = True
        return await self.__repository.save(element)
