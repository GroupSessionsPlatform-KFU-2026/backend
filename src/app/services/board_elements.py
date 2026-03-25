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
        self, filters: BoardElementFilters
    ) -> Sequence[BoardElement]:
        return await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_element(
        self, element_create: BoardElementCreate
    ) -> BoardElement:
        element_dump = element_create.model_dump()
        element = BoardElement(**element_dump, is_deleted=False)
        return await self.__repository.save(element)

    async def update_element(
        self, element_update: BoardElementUpdate, element_id: UUID
    ) -> Optional[BoardElement]:
        return await self.__repository.update(element_id, element_update)

    async def delete_element(
        self, element_id: UUID
    ) -> Optional[BoardElement]:
        element = await self.__repository.get(element_id)
        if element is None:
            return None

        element.is_deleted = True
        return await self.__repository.save(element)