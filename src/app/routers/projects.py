from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.core.responses import auth_responses, detail_responses
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import ProjectServiceDep
from src.app.models.project import ProjectCreate, ProjectPublic, ProjectUpdate
from src.app.models.project_tag import ProjectTagPublic
from src.app.schemas.pagination import PaginatedResponse, build_paginated_response
from src.app.schemas.project_filters import ProjectFilters
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/projects',
    tags=['projects'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['projects:read'])],
    responses=auth_responses,
)
async def get_projects(
    filters: Annotated[ProjectFilters, Query()],
    project_service: ProjectServiceDep,
) -> PaginatedResponse[ProjectPublic]:
    projects = await project_service.get_projects(filters)
    total = await project_service.count_projects(filters)

    return build_paginated_response(
        items=list(projects),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.post(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['projects:write'])],
    responses=auth_responses,
)
async def create_project(
    project_create: ProjectCreate,
    project_service: ProjectServiceDep,
) -> ProjectPublic:
    return await project_service.create_project(project_create)


@router.get(
    '/{project_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:read'])],
    responses={**auth_responses, **detail_responses},
)
async def get_project(
    project_id: UUID,
    project_service: ProjectServiceDep,
) -> ProjectPublic:
    project = await project_service.get_project(project_id)

    if project is None:
        raise NotFoundError

    return project


@router.put(
    '/{project_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:write'])],
    responses={**auth_responses, **detail_responses},
)
async def update_project(
    project_update: ProjectUpdate,
    project_id: UUID,
    project_service: ProjectServiceDep,
) -> ProjectPublic:
    project = await project_service.update_project(project_update, project_id)

    if project is None:
        raise NotFoundError

    return project


@router.delete(
    '/{project_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:delete'])],
    responses={**auth_responses, **detail_responses},
)
async def archive_project(
    project_id: UUID,
    project_service: ProjectServiceDep,
) -> ProjectPublic:
    project = await project_service.archive_project(project_id)

    if project is None:
        raise NotFoundError

    return project


@router.get(
    '/{project_id}/tags',
    dependencies=[Security(require_scoped_user, scopes=['projects:read'])],
    responses={**auth_responses, **detail_responses},
)
async def get_project_tags(
    project_id: UUID,
    project_service: ProjectServiceDep,
) -> Sequence[ProjectTagPublic]:
    return await project_service.get_project_tags(project_id)


@router.post(
    '/{project_id}/tags/{tag_id}',
    dependencies=[Security(require_scoped_user, scopes=['projects:write'])],
    responses={**auth_responses, **detail_responses},
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
    responses={**auth_responses, **detail_responses},
)
async def remove_tag_from_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectServiceDep,
) -> ProjectTagPublic:
    project_tag = await project_service.remove_tag_from_project(project_id, tag_id)

    if project_tag is None:
        raise NotFoundError

    return project_tag
