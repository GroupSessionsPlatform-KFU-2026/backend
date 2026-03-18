from typing import Optional, Sequence

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

    async def create_project(
        self, owner_id: int, project_create: ProjectCreate
    ) -> Project:
        project_dump = project_create.model_dump()
        project = Project(**project_dump, owner_id=owner_id, is_archived=False)
        return await self.__project_repository.save(project)

    async def get_project(self, project_id: int) -> Optional[Project]:
        return await self.__project_repository.get(project_id)

    async def update_project(
        self, project_update: ProjectUpdate, project_id: int
    ) -> Optional[Project]:
        return await self.__project_repository.update(project_id, project_update)

    async def archive_project(self, project_id: int) -> Optional[Project]:
        project = await self.__project_repository.get(project_id)
        if project is None:
            return None
        project.is_archived = True
        return await self.__project_repository.save(project)

    async def get_project_tags(self, project_id: int) -> Sequence[ProjectTag]:
        filters = ProjectTagFilters(project_id=project_id, offset=0, limit=100)
        return await self.__project_tag_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def assign_tag_to_project(self, project_id: int, tag_id: int) -> ProjectTag:
        project_tag = ProjectTag(project_id=project_id, tag_id=tag_id, is_active=True)
        return await self.__project_tag_repository.save(project_tag)

    async def remove_tag_from_project(
        self,
        project_id: int,
        tag_id: int,
    ) -> Optional[ProjectTag]:
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
            return None

        relation = relations[0]
        return await self.__project_tag_repository.delete(relation.id)
