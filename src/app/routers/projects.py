from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import ProjectServiceDep
from src.app.models.project import ProjectCreate, ProjectPublic, ProjectUpdate
from src.app.models.project_tag import ProjectTagPublic
from src.app.schemas.project_filters import ProjectFilters

router = APIRouter(
    prefix='/projects',
    tags=['projects'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['projects:read'])],
)
async def get_projects(
    filters: Annotated[ProjectFilters, Query()],
    project_service: ProjectServiceDep,
) -> Sequence[ProjectPublic]:
    return await project_service.get_projects(filters)


@router.post(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['projects:write'])],
)
async def create_project(
    project_create: ProjectCreate,
    project_service: ProjectServiceDep,
) -> ProjectPublic:
    return await project_service.create_project(project_create)


@router.get(
    '/{project_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:read'])],
)
async def get_project(
    project_id: UUID,
    project_service: ProjectServiceDep,
) -> Optional[ProjectPublic]:
    return await project_service.get_project(project_id)


@router.put(
    '/{project_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:write'])],
)
async def update_project(
    project_update: ProjectUpdate,
    project_id: UUID,
    project_service: ProjectServiceDep,
) -> Optional[ProjectPublic]:
    return await project_service.update_project(project_update, project_id)


@router.delete(
    '/{project_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:delete'])],
)
async def archive_project(
    project_id: UUID,
    project_service: ProjectServiceDep,
) -> Optional[ProjectPublic]:
    return await project_service.archive_project(project_id)


@router.get(
    '/{project_id}/tags',
    dependencies=[Security(require_scoped_user, scopes=['projects:read'])],
)
async def get_project_tags(
    project_id: UUID,
    project_service: ProjectServiceDep,
) -> Sequence[ProjectTagPublic]:
    return await project_service.get_project_tags(project_id)


@router.post(
    '/{project_id}/tags/{tag_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:write'])],
)
async def assign_tag_to_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectServiceDep,
) -> ProjectTagPublic:
    return await project_service.assign_tag_to_project(project_id, tag_id)


@router.delete(
    '/{project_id}/tags/{tag_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:write'])],
)
async def remove_tag_from_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectServiceDep,
) -> Optional[ProjectTagPublic]:
    return await project_service.remove_tag_from_project(project_id, tag_id)
