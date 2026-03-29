from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    ProjectTagRepository,
    ProjectTagRepositoryDep,
)
from src.app.models.project_tag import (
    ProjectTag,
    ProjectTagCreate,
    ProjectTagUpdate,
)
from src.app.schemas.project_tag_filters import ProjectTagFilters


class ProjectTagService:
    __repository: ProjectTagRepository

    def __init__(self, repository: ProjectTagRepositoryDep):
        self.__repository = repository

    async def get_project_tags(
        self,
        filters: ProjectTagFilters,
    ) -> Sequence[ProjectTag]:
        return await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_project_tag(
        self,
        project_tag_create: ProjectTagCreate,
    ) -> ProjectTag:
        project_tag_dump = project_tag_create.model_dump()
        relation = ProjectTag(**project_tag_dump, is_active=True)
        return await self.__repository.save(relation)

    async def update_project_tag(
        self,
        project_tag_update: ProjectTagUpdate,
        relation_id: UUID,
    ) -> Optional[ProjectTag]:
        return await self.__repository.update(relation_id, project_tag_update)

    async def delete_project_tag(self, relation_id: UUID) -> Optional[ProjectTag]:
        return await self.__repository.delete(relation_id)
