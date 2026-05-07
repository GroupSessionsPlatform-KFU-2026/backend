from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status

from src.app.dependencies.repositories import (
    ProjectRepository,
    ProjectRepositoryDep,
    ProjectTagRepository,
    ProjectTagRepositoryDep,
    TagRepository,
    TagRepositoryDep,
)
from src.app.models.project import Project, ProjectCreate, ProjectUpdate
from src.app.models.project_tag import ProjectTag
from src.app.schemas.project_filters import ProjectFilters
from src.app.schemas.project_tag_filters import ProjectTagFilters


class ProjectService:
    __project_repository: ProjectRepository
    __project_tag_repository: ProjectTagRepository
    __tag_repository: TagRepository

    def __init__(
        self,
        project_repository: ProjectRepositoryDep,
        project_tag_repository: ProjectTagRepositoryDep,
        tag_repository: TagRepositoryDep,
    ):
        self.__project_repository = project_repository
        self.__project_tag_repository = project_tag_repository
        self.__tag_repository = tag_repository

    async def get_projects(self, filters: ProjectFilters) -> Sequence[Project]:
        return await self.__project_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    # We should change when will have auth
    async def create_project(self, project_create: ProjectCreate) -> Project:
        project_dump = project_create.model_dump()
        project = Project(**project_dump, is_archived=False)
        return await self.__project_repository.save(project)

    async def get_project(self, project_id: UUID) -> Project:
        project = await self.__project_repository.get(project_id)

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Project not found',
            )

        return project

    async def update_project(
        self, project_update: ProjectUpdate, project_id: UUID
        ) -> Project:
        project = await self.__project_repository.update(project_id, project_update)

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Project not found',
            )

        return project

    async def get_project_tags(self, project_id: UUID) -> Sequence[ProjectTag]:
        filters = ProjectTagFilters(project_id=project_id, offset=0, limit=100)
        return await self.__project_tag_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def assign_tag_to_project(self, project_id: UUID, tag_id: UUID) -> ProjectTag:
        project_tag = ProjectTag(project_id=project_id, tag_id=tag_id, is_active=True)
        return await self.__project_tag_repository.save(project_tag)

    async def remove_tag_from_project(
        self,
        project_id: UUID,
        tag_id: UUID,
    ) -> ProjectTag:
        filters = ProjectTagFilters(
            project_id=project_id,
            tag_id=tag_id,
            offset=0,
            limit=1,
        )
        relations = await self.__project_tag_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

        if not relations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Project tag relation not found',
            )

        relation = relations[0]
        return await self.__project_tag_repository.delete(relation.id)

    async def count_projects(self, filters: ProjectFilters) -> int:
        return await self.__project_repository.count(filters=filters)


    async def count_project_tags(self, project_id: UUID) -> int:
        filters = ProjectTagFilters(project_id=project_id, offset=0, limit=100)
        return await self.__project_tag_repository.count(filters=filters)
