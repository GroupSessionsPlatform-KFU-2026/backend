from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security, Depends
from src.app.dependencies.security import get_current_user
from src.app.services.projects import ProjectService
from src.app.models.user import User
from src.app.models.project import ProjectCreate, ProjectPublic, ProjectUpdate
from src.app.models.project_tag import ProjectTagPublic
from src.app.schemas.project_filters import ProjectFilters

router = APIRouter(
    prefix='/projects',
    tags=['projects'],
)


@router.get('/')
async def get_projects(
    filters: Annotated[ProjectFilters, Query()],
    project_service: ProjectService = Depends(),
    current_user: User = Security(get_current_user, scopes=['projects:read']),
) -> Sequence[ProjectPublic]:
    return await project_service.get_projects(filters)


@router.post('/')
async def create_project(
    project_create: ProjectCreate,
    project_service: ProjectService = Depends(),
    current_user: User = Security(get_current_user, scopes=['projects:write']),
) -> ProjectPublic:
    return await project_service.create_project(project_create)


@router.get('/{project_id}')
async def get_project(
    project_id: UUID,
    project_service: ProjectService = Depends(),
    current_user: User = Security(get_current_user, scopes=['projects:read']),
) -> Optional[ProjectPublic]:
    return await project_service.get_project(project_id)


@router.put('/{project_id}')
async def update_project(
    project_update: ProjectUpdate,
    project_id: UUID,
    project_service: ProjectService = Depends(),
    current_user: User = Security(get_current_user, scopes=['projects:write']),
) -> Optional[ProjectPublic]:
    return await project_service.update_project(project_update, project_id)


@router.delete('/{project_id}')
async def archive_project(
    project_id: UUID,
    project_service: ProjectService = Depends(),
    current_user: User = Security(get_current_user, scopes=['projects:delete']),
) -> Optional[ProjectPublic]:
    return await project_service.archive_project(project_id)


@router.get('/{project_id}/tags')
async def get_project_tags(
    project_id: UUID,
    project_service: ProjectService = Depends(),
    current_user: User = Security(get_current_user, scopes=['projects:read']),
) -> Sequence[ProjectTagPublic]:
    return await project_service.get_project_tags(project_id)


@router.post('/{project_id}/tags/{tag_id}')
async def assign_tag_to_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectService = Depends(),
    current_user: User = Security(get_current_user, scopes=['projects:write']),
) -> ProjectTagPublic:
    return await project_service.assign_tag_to_project(project_id, tag_id)


@router.delete('/{project_id}/tags/{tag_id}')
async def remove_tag_from_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectService = Depends(),
    current_user: User = Security(get_current_user, scopes=['projects:write']),
) -> Optional[ProjectTagPublic]:
    return await project_service.remove_tag_from_project(project_id, tag_id)
