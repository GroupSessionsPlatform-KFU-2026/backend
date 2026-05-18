from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.core.responses import auth_responses, detail_responses
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import ProjectServiceDep
from src.app.models.project import ProjectCreate, ProjectPublic, ProjectUpdate
from src.app.models.project_tag import ProjectTagPublic
from src.app.models.user import User as UserModel
from src.app.schemas.pagination import PaginatedResponse, build_paginated_response
from src.app.schemas.project_filters import ProjectFilters
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/projects',
    tags=['projects'],
)


@router.get(
    '/',
    responses=auth_responses,
)
async def get_projects(
    filters: Annotated[ProjectFilters, Query()],
    project_service: ProjectServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['projects:read']),
    ],
) -> PaginatedResponse[ProjectPublic]:
    filters = filters.model_copy(update={'owner_id': current_user.id})
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
    responses=auth_responses,
)
async def create_project(
    project_create: ProjectCreate,
    project_service: ProjectServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['projects:write']),
    ],
) -> ProjectPublic:
    return await project_service.create_project(project_create, current_user.id)


@router.get(
    '/{project_id}',
    responses={**auth_responses, **detail_responses},
)
async def get_project(
    project_id: UUID,
    project_service: ProjectServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['projects:read']),
    ],
) -> ProjectPublic:
    project = await project_service.get_project(project_id, current_user.id)

    if project is None:
        raise NotFoundError()

    return project


@router.put(
    '/{project_id}',
    responses={**auth_responses, **detail_responses},
)
async def update_project(
    project_update: ProjectUpdate,
    project_id: UUID,
    project_service: ProjectServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['projects:write']),
    ],
) -> ProjectPublic:
    project = await project_service.update_project(
        project_update,
        project_id,
        current_user.id,
    )

    if project is None:
        raise NotFoundError()

    return project


@router.delete(
    '/{project_id}',
    responses={**auth_responses, **detail_responses},
)
async def archive_project(
    project_id: UUID,
    project_service: ProjectServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['projects:delete']),
    ],
) -> ProjectPublic:
    project = await project_service.archive_project(project_id, current_user.id)

    if project is None:
        raise NotFoundError()

    return project


@router.get(
    '/{project_id}/tags',
    responses={**auth_responses, **detail_responses},
)
async def get_project_tags(
    project_id: UUID,
    project_service: ProjectServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['projects:read']),
    ],
) -> Sequence[ProjectTagPublic]:
    return await project_service.get_project_tags(project_id, current_user.id)


@router.post(
    '/{project_id}/tags/{tag_id}',
    responses={**auth_responses, **detail_responses},
)
async def assign_tag_to_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['projects:write']),
    ],
) -> ProjectTagPublic:
    return await project_service.assign_tag_to_project(
        project_id,
        tag_id,
        current_user.id,
    )


@router.delete(
    '/{project_id}/tags/{tag_id}',
    responses={**auth_responses, **detail_responses},
)
async def remove_tag_from_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['projects:write']),
    ],
) -> ProjectTagPublic:
    project_tag = await project_service.remove_tag_from_project(
        project_id,
        tag_id,
        current_user.id,
    )

    if project_tag is None:
        raise NotFoundError()

    return project_tag
