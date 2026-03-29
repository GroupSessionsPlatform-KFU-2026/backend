from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    TagRepository,
    TagRepositoryDep,
)
from src.app.models.tag import Tag, TagCreate, TagUpdate
from src.app.schemas.tag_filters import TagFilters


class TagService:
    __repository: TagRepository

    def __init__(self, repository: TagRepositoryDep):
        self.__repository = repository

    async def get_tags(self, filters: TagFilters) -> Sequence[Tag]:
        return await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_tag(self, tag_create: TagCreate) -> Tag:
        tag_dump = tag_create.model_dump()
        tag = Tag(**tag_dump)
        return await self.__repository.save(tag)

    async def get_tag(self, tag_id: UUID) -> Optional[Tag]:
        return await self.__repository.get(tag_id)

    async def update_tag(
        self,
        tag_update: TagUpdate,
        tag_id: UUID,
    ) -> Optional[Tag]:
        return await self.__repository.update(tag_id, tag_update)

    async def delete_tag(self, tag_id: UUID) -> Optional[Tag]:
        return await self.__repository.delete(tag_id)
